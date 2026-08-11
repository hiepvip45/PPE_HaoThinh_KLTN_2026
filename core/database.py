"""
Database Manager - Quản lý kết nối và thao tác với SQLite
"""
import sqlite3
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import json
import os


class DatabaseManager:
    def __init__(self, db_path: str = 'ppe_guardian.db'):
        self.db_path = db_path
        self.connection = None
        self.init_database()

    def connect(self) -> bool:
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys = ON")
            return True
        except Exception as e:
            print(f"[DB] Lỗi kết nối: {e}")
            return False

    def disconnect(self):
        if self.connection:
            self.connection.close()

    def ensure_connected(self):
        if not self.connection:
            self.connect()

    def execute_query(self, query: str, params=None) -> Optional[int]:
        """Thực thi INSERT/UPDATE/DELETE, trả về lastrowid"""
        try:
            self.ensure_connected()
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            last_id = cursor.lastrowid
            cursor.close()
            return last_id
        except Exception as e:
            print(f"[DB] Lỗi execute: {e}")
            return None

    def fetch_all(self, query: str, params=None) -> List[Dict]:
        """Trả về danh sách dict"""
        try:
            self.ensure_connected()
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            results = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            return results
        except Exception as e:
            print(f"[DB] Lỗi fetch: {e}")
            return []

    def fetch_one(self, query: str, params=None) -> Optional[Dict]:
        results = self.fetch_all(query, params)
        return results[0] if results else None
    
    def init_database(self):
        """Khởi tạo database schema nếu chưa tồn tại"""
        self.connect()
        cursor = self.connection.cursor()
        
        # Bảng cấu hình hệ thống
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT NOT NULL UNIQUE,
                config_value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Bảng lịch sử phát hiện
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                source_type TEXT NOT NULL CHECK(source_type IN ('webcam', 'video', 'image')),
                source_name TEXT,
                detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_persons INTEGER DEFAULT 0,
                has_violation INTEGER DEFAULT 0,
                image_path TEXT,
                frame_number INTEGER DEFAULT 0,
                confidence_avg REAL DEFAULT 0.0
            )
        """)
        
        # Bảng chi tiết từng đối tượng phát hiện
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detection_objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detection_id INTEGER NOT NULL,
                class_name TEXT NOT NULL,
                confidence REAL NOT NULL,
                bbox_x1 REAL, bbox_y1 REAL,
                bbox_x2 REAL, bbox_y2 REAL,
                is_violation INTEGER DEFAULT 0,
                FOREIGN KEY (detection_id) REFERENCES detections(id) ON DELETE CASCADE
            )
        """)
        
        # Bảng vi phạm
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detection_id INTEGER NOT NULL,
                violation_type TEXT NOT NULL,
                violation_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                image_path TEXT,
                telegram_sent INTEGER DEFAULT 0,
                telegram_sent_at DATETIME NULL,
                source_type TEXT NOT NULL CHECK(source_type IN ('webcam', 'video', 'image')),
                source_name TEXT,
                confidence REAL DEFAULT 0.0,
                FOREIGN KEY (detection_id) REFERENCES detections(id) ON DELETE CASCADE
            )
        """)
        
        # Bảng thống kê theo ngày
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_date DATE NOT NULL UNIQUE,
                total_detections INTEGER DEFAULT 0,
                total_violations INTEGER DEFAULT 0,
                total_persons INTEGER DEFAULT 0,
                compliance_rate REAL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tạo index
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_detections_date ON detections(detected_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_violations_date ON violations(violation_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_violations_type ON violations(violation_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_detection_objects_class ON detection_objects(class_name)")
        
        # Thêm cấu hình mặc định
        default_configs = [
            ('telegram_bot_token', ''),
            ('telegram_chat_id', ''),
            ('alert_cooldown_seconds', '30'),
            ('confidence_threshold', '0.5'),
            ('violation_classes', 'NO-Gloves,NO-Goggles,NO-Hardhat,NO-Mask,NO-Safety Vest,Fall-Detected'),
            ('capture_violations', '1'),
            ('send_telegram', '1')
        ]
        
        for key, value in default_configs:
            cursor.execute("""
                INSERT OR IGNORE INTO system_config (config_key, config_value) 
                VALUES (?, ?)
            """, (key, value))
        
        self.connection.commit()
        cursor.close()

    # ─── DETECTIONS ───────────────────────────────────────────────
    def save_detection(self, session_id: str, source_type: str, source_name: str,
                       total_persons: int, has_violation: bool, image_path: str,
                       frame_number: int, confidence_avg: float) -> Optional[int]:
        query = """
            INSERT INTO detections 
            (session_id, source_type, source_name, total_persons, has_violation, 
             image_path, frame_number, confidence_avg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute_query(query, (
            session_id, source_type, source_name, total_persons,
            has_violation, image_path, frame_number, confidence_avg
        ))

    def save_detection_objects(self, detection_id: int, objects: List[Dict]):
        query = """
            INSERT INTO detection_objects 
            (detection_id, class_name, confidence, bbox_x1, bbox_y1, bbox_x2, bbox_y2, is_violation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            self.ensure_connected()
            cursor = self.connection.cursor()
            for obj in objects:
                cursor.execute(query, (
                    detection_id, obj['class_name'], obj['confidence'],
                    obj['bbox_x1'], obj['bbox_y1'], obj['bbox_x2'], obj['bbox_y2'],
                    obj['is_violation']
                ))
            self.connection.commit()
            cursor.close()
        except Exception as e:
            print(f"[DB] Lỗi save objects: {e}")

    # ─── VIOLATIONS ───────────────────────────────────────────────
    def save_violation(self, detection_id: int, violation_type: str, image_path: str,
                       source_type: str, source_name: str, confidence: float) -> Optional[int]:
        query = """
            INSERT INTO violations 
            (detection_id, violation_type, image_path, source_type, source_name, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        vid = self.execute_query(query, (
            detection_id, violation_type, image_path, source_type, source_name, confidence
        ))
        self._update_daily_stats(date.today())
        return vid

    def update_telegram_sent(self, violation_id: int):
        query = """
            UPDATE violations SET telegram_sent=1, telegram_sent_at=CURRENT_TIMESTAMP
            WHERE id=?
        """
        self.execute_query(query, (violation_id,))

    def get_violations(self, start_date=None, end_date=None,
                       violation_type=None, limit=500, offset=0) -> List[Dict]:
        conditions = ["1=1"]
        params = []
        if start_date:
            conditions.append("DATE(violation_at) >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("DATE(violation_at) <= ?")
            params.append(end_date)
        if violation_type and violation_type != "Tất cả":
            conditions.append("violation_type = ?")
            params.append(violation_type)
        where = " AND ".join(conditions)
        params.extend([limit, offset])
        query = f"""
            SELECT id, violation_type, violation_at, source_type, source_name,
                   confidence, telegram_sent, image_path
            FROM violations
            WHERE {where}
            ORDER BY violation_at DESC
            LIMIT ? OFFSET ?
        """
        return self.fetch_all(query, params)

    def count_violations(self, start_date=None, end_date=None, violation_type=None) -> int:
        conditions = ["1=1"]
        params = []
        if start_date:
            conditions.append("DATE(violation_at) >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("DATE(violation_at) <= ?")
            params.append(end_date)
        if violation_type and violation_type != "Tất cả":
            conditions.append("violation_type = ?")
            params.append(violation_type)
        where = " AND ".join(conditions)
        row = self.fetch_one(f"SELECT COUNT(*) as cnt FROM violations WHERE {where}", params)
        return row['cnt'] if row else 0

    # ─── STATISTICS ───────────────────────────────────────────────
    def get_violations_by_day(self, days=30) -> List[Dict]:
        query = """
            SELECT DATE(violation_at) as day, COUNT(*) as count
            FROM violations
            WHERE violation_at >= datetime('now', '-' || ? || ' days')
            GROUP BY DATE(violation_at)
            ORDER BY day ASC
        """
        return self.fetch_all(query, (days,))

    def get_violations_by_type(self, days=30) -> List[Dict]:
        query = """
            SELECT violation_type, COUNT(*) as count
            FROM violations
            WHERE violation_at >= datetime('now', '-' || ? || ' days')
            GROUP BY violation_type
            ORDER BY count DESC
        """
        return self.fetch_all(query, (days,))

    def get_compliance_stats(self, days=7) -> Dict:
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN has_violation=0 THEN 1 ELSE 0 END) as compliant,
                SUM(CASE WHEN has_violation=1 THEN 1 ELSE 0 END) as violated,
                AVG(total_persons) as avg_persons
            FROM detections
            WHERE detected_at >= datetime('now', '-' || ? || ' days')
            AND total_persons > 0
        """
        return self.fetch_one(query, (days,)) or {}

    def get_summary_today(self) -> Dict:
        query = """
            SELECT 
                COUNT(DISTINCT d.id) as total_detections,
                SUM(d.total_persons) as total_persons,
                COUNT(v.id) as total_violations
            FROM detections d
            LEFT JOIN violations v ON v.detection_id = d.id 
                AND DATE(v.violation_at) = DATE('now')
            WHERE DATE(d.detected_at) = DATE('now')
        """
        return self.fetch_one(query) or {}

    def get_weekly_violations(self) -> List[Dict]:
        query = """
            SELECT 
                strftime('%Y-W%W', violation_at) as week_key,
                MIN(DATE(violation_at)) as week_start,
                COUNT(*) as count
            FROM violations
            WHERE violation_at >= datetime('now', '-12 weeks')
            GROUP BY strftime('%Y-W%W', violation_at)
            ORDER BY week_key ASC
        """
        return self.fetch_all(query)

    def get_monthly_violations(self) -> List[Dict]:
        query = """
            SELECT 
                strftime('%Y-%m', violation_at) as month,
                COUNT(*) as count
            FROM violations
            WHERE violation_at >= datetime('now', '-12 months')
            GROUP BY strftime('%Y-%m', violation_at)
            ORDER BY month ASC
        """
        return self.fetch_all(query)

    def export_violations_csv(self, start_date=None, end_date=None,
                               violation_type=None) -> List[Dict]:
        return self.get_violations(start_date, end_date, violation_type, limit=99999)

    # ─── CONFIG ───────────────────────────────────────────────────
    def get_config(self, key: str) -> Optional[str]:
        row = self.fetch_one(
            "SELECT config_value FROM system_config WHERE config_key=?", (key,)
        )
        return row['config_value'] if row else None

    def set_config(self, key: str, value: str):
        query = """
            INSERT OR REPLACE INTO system_config (config_key, config_value) 
            VALUES (?, ?)
        """
        self.execute_query(query, (key, value))

    def get_all_configs(self) -> Dict:
        rows = self.fetch_all("SELECT config_key, config_value FROM system_config")
        return {r['config_key']: r['config_value'] for r in rows}

    def _update_daily_stats(self, stat_date: date):
        query = """
            INSERT OR REPLACE INTO daily_stats (stat_date, total_detections, total_violations, compliance_rate)
            SELECT 
                ?,
                COUNT(DISTINCT d.id),
                COUNT(DISTINCT v.id),
                CASE WHEN COUNT(DISTINCT d.id) > 0 
                     THEN (COUNT(DISTINCT d.id) - COUNT(DISTINCT v.id)) * 100.0 / COUNT(DISTINCT d.id)
                     ELSE 100 END
            FROM detections d
            LEFT JOIN violations v ON v.detection_id = d.id AND DATE(v.violation_at) = DATE(?)
            WHERE DATE(d.detected_at) = DATE(?)
        """
        self.execute_query(query, (stat_date, stat_date, stat_date))
