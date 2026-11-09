"""
Module Database: Hỗ trợ linh hoạt cả SQLite (chạy cục bộ/Persistent Disk) 
và PostgreSQL (khi chạy online với Supabase, Neon hoặc Render Postgres qua DATABASE_URL).
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "quota_system.db"))
DATABASE_URL = os.environ.get("DATABASE_URL")

# Chuẩn hóa tiền tố DATABASE_URL từ postgres:// thành postgresql:// nếu có
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def is_postgres() -> bool:
    return bool(DATABASE_URL and DATABASE_URL.startswith("postgresql://"))

def get_connection():
    if is_postgres():
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    if is_postgres():
        # Schema cho PostgreSQL
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            code VARCHAR(20) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT
        );
        """)
        cursor.execute("""
        INSERT INTO projects (code, name, description)
        VALUES 
            ('0747', 'Dự án Nghiên cứu Ô tô 0747', 'Bảng hỏi 1 - Dự án ô tô toàn quốc'),
            ('0748', 'Dự án Nghiên cứu Ô tô 0748', 'Bảng hỏi 2 - Dự án ô tô toàn quốc')
        ON CONFLICT (code) DO NOTHING;
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quota_uploads (
            id SERIAL PRIMARY KEY,
            project_code VARCHAR(20) NOT NULL,
            quota_date VARCHAR(20) NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            file_path TEXT NOT NULL,
            uploaded_at VARCHAR(30) NOT NULL,
            total_achieved INTEGER DEFAULT 0,
            total_target INTEGER DEFAULT 0,
            parsed_json TEXT,
            UNIQUE(project_code, quota_date),
            FOREIGN KEY(project_code) REFERENCES projects(code)
        );
        """)
    else:
        # Schema cho SQLite
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT
        );
        """)
        cursor.execute("""
        INSERT INTO projects (code, name, description)
        VALUES 
            ('0747', 'Dự án Nghiên cứu Ô tô 0747', 'Bảng hỏi 1 - Dự án ô tô toàn quốc'),
            ('0748', 'Dự án Nghiên cứu Ô tô 0748', 'Bảng hỏi 2 - Dự án ô tô toàn quốc')
        ON CONFLICT (code) DO NOTHING;
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quota_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_code TEXT NOT NULL,
            quota_date TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            uploaded_at TEXT NOT NULL,
            total_achieved INTEGER DEFAULT 0,
            total_target INTEGER DEFAULT 0,
            parsed_json TEXT,
            UNIQUE(project_code, quota_date),
            FOREIGN KEY(project_code) REFERENCES projects(code)
        );
        """)
    
    conn.commit()
    conn.close()

def save_upload(project_code: str, quota_date: str, file_name: str, file_path: str, parsed_data: Dict[str, Any]) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tính tổng từ dòng TOTAL
    total_achieved = 0
    total_target = 0
    for r in parsed_data.get("rows", []):
        if r.get("is_total"):
            total_achieved, total_target, _ = r.get("total", (0, 0, 0))
            break
            
    parsed_json = json.dumps(parsed_data, ensure_ascii=False)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    ph = "%s" if is_postgres() else "?"
    query = f"""
    INSERT INTO quota_uploads (project_code, quota_date, file_name, file_path, uploaded_at, total_achieved, total_target, parsed_json)
    VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
    ON CONFLICT(project_code, quota_date) DO UPDATE SET
        file_name = excluded.file_name,
        file_path = excluded.file_path,
        uploaded_at = excluded.uploaded_at,
        total_achieved = excluded.total_achieved,
        total_target = excluded.total_target,
        parsed_json = excluded.parsed_json;
    """
    
    cursor.execute(query, (project_code, quota_date, file_name, file_path, now_str, total_achieved, total_target, parsed_json))
    
    upload_id = getattr(cursor, "lastrowid", 1)
    conn.commit()
    conn.close()
    return upload_id

def get_available_dates(project_code: str) -> List[str]:
    conn = get_connection()
    cursor = conn.cursor()
    ph = "%s" if is_postgres() else "?"
    cursor.execute(f"""
    SELECT DISTINCT quota_date FROM quota_uploads
    WHERE project_code = {ph}
    ORDER BY quota_date DESC;
    """, (project_code,))
    
    rows = cursor.fetchall()
    conn.close()
    if is_postgres():
        return [r[0] for r in rows]
    else:
        return [r["quota_date"] for r in rows]

def get_upload_data(project_code: str, quota_date: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    ph = "%s" if is_postgres() else "?"
    cursor.execute(f"""
    SELECT * FROM quota_uploads
    WHERE project_code = {ph} AND quota_date = {ph};
    """, (project_code, quota_date))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    if is_postgres():
        # Postgres mapping
        col_names = [desc[0] for desc in cursor.description]
        data_dict = dict(zip(col_names, row))
    else:
        data_dict = dict(row)
        
    if data_dict.get("parsed_json"):
        return {
            "id": data_dict["id"],
            "project_code": data_dict["project_code"],
            "quota_date": data_dict["quota_date"],
            "file_name": data_dict["file_name"],
            "file_path": data_dict["file_path"],
            "uploaded_at": data_dict["uploaded_at"],
            "total_achieved": data_dict["total_achieved"],
            "total_target": data_dict["total_target"],
            "parsed_data": json.loads(data_dict["parsed_json"])
        }
    return None

def get_all_uploads_summary() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, project_code, quota_date, file_name, uploaded_at, total_achieved, total_target
    FROM quota_uploads
    ORDER BY quota_date DESC, project_code ASC;
    """)
    rows = cursor.fetchall()
    conn.close()
    
    if is_postgres():
        col_names = [desc[0] for desc in cursor.description]
        return [dict(zip(col_names, r)) for r in rows]
    else:
        return [dict(r) for r in rows]

if __name__ == "__main__":
    init_db()
    if is_postgres():
        print("Khoi tao Database thanh cong tren Cloud PostgreSQL!")
    else:
        print("Khoi tao Database thanh cong tai:", DB_PATH)
