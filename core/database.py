"""
Database Manager - Quản lý kết nối và thao tác với MySQL
"""
import mysql.connector
from mysql.connector import Error
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import json


class DatabaseManager:
    def __init__(self, host='localhost', port=3306, database='ppe_guardian',
                 user='root', password=''):
        self.config = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password,
            'charset': 'utf8mb4',
            'autocommit': True,
            'connection_timeout': 10
        }
        self.connection = None

    def connect(self) -> bool:
        try:
            self.connection = mysql.connector.connect(**self.config)
            return self.connection.is_connected()
        except Error as e:
            print(f"[DB] Lỗi kết nối: {e}")
            return False

    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def ensure_connected(self):
        if not self.connection or not self.connection.is_connected():
            self.connect()

    def execute_query(self, query: str, params=None) -> Optional[int]:
        """Thực thi INSERT/UPDATE/DELETE, trả về lastrowid"""
        try:
            self.ensure_connected()
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            last_id = cursor.lastrowid
            cursor.close()
            return last_id
        except Error as e:
            print(f"[DB] Lỗi execute: {e}")
            return None

    def fetch_all(self, query: str, params=None) -> List[Dict]:
        """Trả về danh sách dict"""
        try:
            self.ensure_connected()
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            print(f"[DB] Lỗi fetch: {e}")
            return []

    def fetch_one(self, query: str, params=None) -> Optional[Dict]:
        results = self.fetch_all(query, params)
        return results[0] if results else None

    # ─── DETECTIONS ───────────────────────────────────────────────
    def save_detection(self, session_id: str, source_type: str, source_name: str,
                       total_persons: int, has_violation: bool, image_path: str,
                       frame_number: int, confidence_avg: float) -> Optional[int]:
        query = """
            INSERT INTO detections 
            (session_id, source_type, source_name, total_persons, has_violation, 
             image_path, frame_number, confidence_avg)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute_query(query, (
            session_id, source_type, source_name, total_persons,
            has_violation, image_path, frame_number, confidence_avg
        ))

    def save_detection_objects(self, detection_id: int, objects: List[Dict]):
        query = """
            INSERT INTO detection_objects 
            (detection_id, class_name, confidence, bbox_x1, bbox_y1, bbox_x2, bbox_y2, is_violation)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
            cursor.close()
        except Error as e:
            print(f"[DB] Lỗi save objects: {e}")

    # ─── VIOLATIONS ───────────────────────────────────────────────
    def save_violation(self, detection_id: int, violation_type: str, image_path: str,
                       source_type: str, source_name: str, confidence: float) -> Optional[int]:
        query = """
            INSERT INTO violations 
            (detection_id, violation_type, image_path, source_type, source_name, confidence)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        vid = self.execute_query(query, (
            detection_id, violation_type, image_path, source_type, source_name, confidence
        ))
        self._update_daily_stats(date.today())
        return vid

    def update_telegram_sent(self, violation_id: int):
        query = """
            UPDATE violations SET telegram_sent=TRUE, telegram_sent_at=NOW()
            WHERE id=%s
        """
        self.execute_query(query, (violation_id,))

    def get_violations(self, start_date=None, end_date=None,
                       violation_type=None, limit=500, offset=0) -> List[Dict]:
        conditions = ["1=1"]
        params = []
        if start_date:
            conditions.append("violation_at >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("violation_at <= %s")
            params.append(end_date)
        if violation_type and violation_type != "Tất cả":
            conditions.append("violation_type = %s")
            params.append(violation_type)
        where = " AND ".join(conditions)
        params.extend([limit, offset])
        query = f"""
            SELECT id, violation_type, violation_at, source_type, source_name,
                   confidence, telegram_sent, image_path
            FROM violations
            WHERE {where}
            ORDER BY violation_at DESC
            LIMIT %s OFFSET %s
        """
        return self.fetch_all(query, params)

    def count_violations(self, start_date=None, end_date=None, violation_type=None) -> int:
        conditions = ["1=1"]
        params = []
        if start_date:
            conditions.append("violation_at >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("violation_at <= %s")
            params.append(end_date)
        if violation_type and violation_type != "Tất cả":
            conditions.append("violation_type = %s")
            params.append(violation_type)
        where = " AND ".join(conditions)
        row = self.fetch_one(f"SELECT COUNT(*) as cnt FROM violations WHERE {where}", params)
        return row['cnt'] if row else 0

    # ─── STATISTICS ───────────────────────────────────────────────
    def get_violations_by_day(self, days=30) -> List[Dict]:
        query = """
            SELECT DATE(violation_at) as day, COUNT(*) as count
            FROM violations
            WHERE violation_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY DATE(violation_at)
            ORDER BY day ASC
        """
        return self.fetch_all(query, (days,))

    def get_violations_by_type(self, days=30) -> List[Dict]:
        query = """
            SELECT violation_type, COUNT(*) as count
            FROM violations
            WHERE violation_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY violation_type
            ORDER BY count DESC
        """
        return self.fetch_all(query, (days,))

    def get_compliance_stats(self, days=7) -> Dict:
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN has_violation=FALSE THEN 1 ELSE 0 END) as compliant,
                SUM(CASE WHEN has_violation=TRUE THEN 1 ELSE 0 END) as violated,
                AVG(total_persons) as avg_persons
            FROM detections
            WHERE detected_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
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
                AND DATE(v.violation_at) = CURDATE()
            WHERE DATE(d.detected_at) = CURDATE()
        """
        return self.fetch_one(query) or {}

    def get_weekly_violations(self) -> List[Dict]:
        query = """
            SELECT 
                YEARWEEK(violation_at, 1) as week_key,
                MIN(DATE(violation_at)) as week_start,
                COUNT(*) as count
            FROM violations
            WHERE violation_at >= DATE_SUB(NOW(), INTERVAL 12 WEEK)
            GROUP BY YEARWEEK(violation_at, 1)
            ORDER BY week_key ASC
        """
        return self.fetch_all(query)

    def get_monthly_violations(self) -> List[Dict]:
        query = """
            SELECT 
                DATE_FORMAT(violation_at, '%Y-%m') as month,
                COUNT(*) as count
            FROM violations
            WHERE violation_at >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
            GROUP BY DATE_FORMAT(violation_at, '%Y-%m')
            ORDER BY month ASC
        """
        return self.fetch_all(query)

    def export_violations_csv(self, start_date=None, end_date=None,
                               violation_type=None) -> List[Dict]:
        return self.get_violations(start_date, end_date, violation_type, limit=99999)

    # ─── CONFIG ───────────────────────────────────────────────────
    def get_config(self, key: str) -> Optional[str]:
        row = self.fetch_one(
            "SELECT config_value FROM system_config WHERE config_key=%s", (key,)
        )
        return row['config_value'] if row else None

    def set_config(self, key: str, value: str):
        query = """
            INSERT INTO system_config (config_key, config_value) VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE config_value=%s
        """
        self.execute_query(query, (key, value, value))

    def get_all_configs(self) -> Dict:
        rows = self.fetch_all("SELECT config_key, config_value FROM system_config")
        return {r['config_key']: r['config_value'] for r in rows}

    def _update_daily_stats(self, stat_date: date):
        query = """
            INSERT INTO daily_stats (stat_date, total_detections, total_violations, compliance_rate)
            SELECT 
                %s,
                COUNT(DISTINCT d.id),
                COUNT(DISTINCT v.id),
                CASE WHEN COUNT(DISTINCT d.id) > 0 
                     THEN (COUNT(DISTINCT d.id) - COUNT(DISTINCT v.id)) / COUNT(DISTINCT d.id) * 100
                     ELSE 100 END
            FROM detections d
            LEFT JOIN violations v ON v.detection_id = d.id AND DATE(v.violation_at) = %s
            WHERE DATE(d.detected_at) = %s
            ON DUPLICATE KEY UPDATE
                total_detections=VALUES(total_detections),
                total_violations=VALUES(total_violations),
                compliance_rate=VALUES(compliance_rate)
        """
        self.execute_query(query, (stat_date, stat_date, stat_date))
