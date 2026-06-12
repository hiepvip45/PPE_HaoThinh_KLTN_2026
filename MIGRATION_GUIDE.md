# SQLite Migration Guide - PPE Guardian

**Migration Date:** June 1, 2026  
**Status:** ✅ COMPLETED

## Summary
Successfully migrated PPE Guardian from MySQL to SQLite for improved portability and simplified deployment.

---

## 📋 What Changed

### Removed Dependencies
- ❌ `mysql-connector-python>=8.1.0` → SQLite3 is built-in with Python

### Database Files Modified

#### 1. **core/database.py** (Complete rewrite)
**Old:** MySQL connection with host/port/user/password  
**New:** SQLite file-based with automatic schema initialization

**Key Changes:**
- Import: `mysql.connector` → `sqlite3`
- Connection: TCP socket → Local file path
- Queries: All MySQL-specific syntax → SQLite equivalents
  - `%s` placeholders → `?`
  - `NOW()` → `CURRENT_TIMESTAMP` / `datetime('now')`
  - `DATE_SUB()` → `datetime('now', '-X days')`
  - `BOOLEAN` → `INTEGER (0/1)`
  - `ON DUPLICATE KEY UPDATE` → `INSERT OR REPLACE`

#### 2. **core/config_manager.py**
**Old Config Keys:**
```python
db_host, db_port, db_name, db_user, db_password
```

**New Config Keys:**
```python
db_path = "ppe_guardian.db"  # Single file path
```

#### 3. **ui/main_window.py**
**Old:**
```python
self.db = DatabaseManager(
    host='localhost',
    port=3306,
    database='ppe_guardian',
    user='root',
    password=''
)
```

**New:**
```python
self.db = DatabaseManager(
    db_path=self.config.get('db_path', 'ppe_guardian.db')
)
```

#### 4. **ui/pages/settings.py**
- Removed: MySQL connection test & configuration UI
- Added: SQLite file browser for database path selection
- Removed: `import mysql.connector`

#### 5. **requirements.txt**
```diff
- mysql-connector-python>=8.1.0
+ # SQLite3 is built-in with Python
```

---

## 🗄️ Database Schema

SQLite database automatically creates 6 tables on startup:

| Table | Purpose |
|-------|---------|
| `system_config` | Configuration key-value store |
| `detections` | PPE detection records |
| `detection_objects` | Individual detected objects |
| `violations` | Safety violations |
| `daily_stats` | Daily statistics cache |
| `sqlite_sequence` | Auto-increment sequences |

All tables include proper:
- ✅ Foreign key constraints
- ✅ Indexes for performance
- ✅ CHECK constraints for data validation
- ✅ DEFAULT values

---

## 🚀 First Run Instructions

1. **Start the app normally**
   ```bash
   python main.py
   ```

2. **Database auto-creation**
   - App will automatically create `ppe_guardian.db` in the project directory
   - All tables and indexes are created on startup
   - Default configurations are inserted

3. **No manual setup needed!**
   - No MySQL server installation
   - No database creation scripts
   - No user/password configuration

---

## 📝 Configuration

### Default Location
```
e:\ppe_guardian\ppe_guardian.db
```

### Custom Location
In Settings → Database tab:
1. Click "📂 Chọn file DB"
2. Select or create a database file
3. Click "💾 Lưu cấu hình DB"
4. Restart the app

### Configuration File
Settings are saved in `app_config.json`:
```json
{
  "db_path": "ppe_guardian.db",
  "telegram_bot_token": "...",
  "...": "..."
}
```

---

## ✅ Verification Checklist

- [x] All MySQL imports removed
- [x] All SQL queries converted to SQLite syntax
- [x] Database auto-initialization working
- [x] Table creation tested and working
- [x] Insert/Query operations tested and working
- [x] Configuration updated for SQLite
- [x] UI settings updated for file-based DB
- [x] No external dependencies added
- [x] Backward compatibility maintained (all functions work the same)

---

## 🔄 Migration Paths

### For Fresh Installation
1. Simply run: `python main.py`
2. Database automatically initializes

### For Existing MySQL Data
If you need to migrate existing data:

1. Export MySQL data to CSV
2. Use SQLite import tools or Python script
3. Or start fresh with SQLite (data will be recorded going forward)

---

## 💾 Backup & Portability

### Benefits
- **Simple Backup:** Copy `ppe_guardian.db` file
- **Portable:** Move database between computers (same directory)
- **Version Control:** Can be tracked in git (if anonymized)
- **No Server:** Run anywhere Python is installed

### Backup Example
```bash
# Backup database
copy ppe_guardian.db ppe_guardian_backup_$(date).db

# Restore from backup
copy ppe_guardian_backup_XXXXXX.db ppe_guardian.db
```

---

## 🐛 Troubleshooting

### Issue: Database file not created
**Solution:** Ensure write permissions in the project directory

### Issue: "Database is locked"
**Solution:** 
- Only one instance of the app can access the DB at a time
- Close other instances and retry

### Issue: Missing tables
**Solution:** Delete `ppe_guardian.db` and restart app - it will recreate

---

## 📞 Support
All database functionality remains the same. If you encounter issues:
1. Check write permissions on the project directory
2. Ensure only one instance of the app is running
3. Delete the database file and restart to recreate

**Status:** ✅ Ready for production use
