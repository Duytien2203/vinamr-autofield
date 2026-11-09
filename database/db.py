"""
Module Database: Hỗ trợ linh hoạt 3 loại cơ sở dữ liệu:
1. Google Cloud Firestore (Firebase) - Khi có file firebase_key.json hoặc biến FIREBASE_CREDENTIALS.
2. PostgreSQL Cloud (Supabase / Neon / Render Postgres) - Khi có biến DATABASE_URL.
3. SQLite (Cục bộ & Persistent Disk) - Mặc định cho phát triển và offline.
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

if os.environ.get("VERCEL"):
    _default_db = "/tmp/quota_system.db"
else:
    _default_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "quota_system.db")
DB_PATH = os.environ.get("DB_PATH", _default_db)
DATABASE_URL = os.environ.get("DATABASE_URL")

# Chuẩn hóa tiền tố DATABASE_URL từ postgres:// thành postgresql:// nếu có
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ==========================================
# 1. KẾT NỐI FIREBASE FIRESTORE
# ==========================================
_firestore_db = None

def get_firestore_client():
    global _firestore_db
    if _firestore_db is not None:
        return _firestore_db
        
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        # A. Kiểm tra biến môi trường FIREBASE_CREDENTIALS (chuỗi JSON trực tiếp)
        env_creds = os.environ.get("FIREBASE_CREDENTIALS")
        if env_creds:
            cred_dict = json.loads(env_creds)
            cred = credentials.Certificate(cred_dict)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            _firestore_db = firestore.client()
            return _firestore_db
            
        # B. Kiểm tra các đường dẫn file key
        key_env = os.environ.get("FIREBASE_KEY_PATH", "")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = [
            key_env,
            "firebase_key.json",
            "serviceAccountKey.json",
            os.path.join(base_dir, "firebase_key.json"),
            os.path.join(base_dir, "serviceAccountKey.json")
        ]
        for p in candidates:
            if p and os.path.exists(p):
                cred = credentials.Certificate(p)
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(cred)
                _firestore_db = firestore.client()
                return _firestore_db
    except Exception as e:
        print("[Firebase Init Warning]:", e)
        
    return None

def is_firebase() -> bool:
    return get_firestore_client() is not None

def is_postgres() -> bool:
    return bool(not is_firebase() and DATABASE_URL and DATABASE_URL.startswith("postgresql://"))

# ==========================================
# 2. KẾT NỐI RELATIONAL DB (Postgres / SQLite)
# ==========================================
def get_connection():
    if is_postgres():
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

# ==========================================
# 3. CÁC HÀM XỬ LÝ DỮ LIỆU ĐA NỀN TẢNG
# ==========================================
def init_db():
    if is_firebase():
        fs = get_firestore_client()
        # Đăng ký sẵn 2 dự án chuẩn vào collection 'projects'
        projects_ref = fs.collection("projects")
        projects_ref.document("0747").set({
            "code": "0747",
            "name": "Dự án Nghiên cứu Ô tô 0747",
            "description": "Bảng hỏi 1 - Dự án ô tô toàn quốc"
        }, merge=True)
        projects_ref.document("0748").set({
            "code": "0748",
            "name": "Dự án Nghiên cứu Ô tô 0748",
            "description": "Bảng hỏi 2 - Dự án ô tô toàn quốc"
        }, merge=True)
        return

    conn = get_connection()
    cursor = conn.cursor()
    
    if is_postgres():
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
    total_achieved = 0
    total_target = 0
    for r in parsed_data.get("rows", []):
        if r.get("is_total"):
            total_achieved, total_target, _ = r.get("total", (0, 0, 0))
            break
            
    parsed_json = json.dumps(parsed_data, ensure_ascii=False)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # A. Lưu vào Firebase Firestore
    if is_firebase():
        fs = get_firestore_client()
        doc_id = f"{project_code}_{quota_date}"
        fs.collection("quota_uploads").document(doc_id).set({
            "project_code": project_code,
            "quota_date": quota_date,
            "file_name": file_name,
            "file_path": file_path,
            "uploaded_at": now_str,
            "total_achieved": total_achieved,
            "total_target": total_target,
            "parsed_json": parsed_json,
        })
        return 1

    # B. Lưu vào PostgreSQL / SQLite
    conn = get_connection()
    cursor = conn.cursor()
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
    # A. Lấy từ Firebase Firestore
    if is_firebase():
        fs = get_firestore_client()
        docs = fs.collection("quota_uploads").where("project_code", "==", project_code).stream()
        dates = []
        for d in docs:
            data = d.to_dict()
            if "quota_date" in data:
                dates.append(data["quota_date"])
        dates.sort(reverse=True)
        return dates

    # B. Lấy từ PostgreSQL / SQLite
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
    # A. Lấy từ Firebase Firestore
    if is_firebase():
        fs = get_firestore_client()
        doc_id = f"{project_code}_{quota_date}"
        doc = fs.collection("quota_uploads").document(doc_id).get()
        if doc.exists:
            data = doc.to_dict()
            return {
                "id": doc.id,
                "project_code": data["project_code"],
                "quota_date": data["quota_date"],
                "file_name": data["file_name"],
                "file_path": data.get("file_path", ""),
                "uploaded_at": data.get("uploaded_at", ""),
                "total_achieved": data.get("total_achieved", 0),
                "total_target": data.get("total_target", 0),
                "parsed_data": json.loads(data["parsed_json"])
            }
        return None

    # B. Lấy từ PostgreSQL / SQLite
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
    # A. Lấy từ Firebase Firestore
    if is_firebase():
        fs = get_firestore_client()
        docs = fs.collection("quota_uploads").stream()
        res = []
        for d in docs:
            data = d.to_dict()
            res.append({
                "id": d.id,
                "project_code": data["project_code"],
                "quota_date": data["quota_date"],
                "file_name": data["file_name"],
                "uploaded_at": data.get("uploaded_at", ""),
                "total_achieved": data.get("total_achieved", 0),
                "total_target": data.get("total_target", 0)
            })
        res.sort(key=lambda x: (x["quota_date"], x["project_code"]), reverse=True)
        return res

    # B. Lấy từ PostgreSQL / SQLite
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
    if is_firebase():
        print("Khoi tao thanh cong voi Google Cloud Firestore (Firebase)!")
    elif is_postgres():
        print("Khoi tao thanh cong tren Cloud PostgreSQL!")
    else:
        print("Khoi tao thanh cong voi SQLite tai:", DB_PATH)
