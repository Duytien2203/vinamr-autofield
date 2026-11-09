"""
VINAMR AutoField Server - API & Web Server chạy trên nền Starlette & Uvicorn.
Cung cấp giao diện Web SPA hiện đại và các API phân tích, xuất báo cáo.
"""

import os
import sys
import mimetypes

# Khắc phục quyền đọc Registry trên Windows sandbox
if hasattr(mimetypes, "_mimetypes_read_windows_registry"):
    mimetypes._mimetypes_read_windows_registry = lambda add_type: None

import json
from datetime import datetime
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from core.parser import QuotaParser, extract_metadata_from_filename
from core.engine import QuotaEngine
from core.reporter import QuotaReporter
from database.db import init_db, save_upload, get_available_dates, get_upload_data, get_all_uploads_summary

# Khởi tạo DB
init_db()

def bootstrap_sample_data():
    dates = get_available_dates("0747")
    if not dates:
        sample_path = os.path.join(BASE_DIR, "data", "samples", "sample_quota_0747_20261106.xml")
        if os.path.exists(sample_path):
            parsed = QuotaParser.parse_xml_spreadsheet(sample_path)
            save_upload("0747", "2026-11-06", "file quota 06/11", sample_path, parsed)

# 1. Trang chủ SPA
async def homepage(request: Request):
    index_path = os.path.join(BASE_DIR, "templates", "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content)

# 2. API Danh sách dự án
async def api_projects(request: Request):
    return JSONResponse({
        "projects": [
            {"code": "0747", "name": "Dự án Ô tô 0747 (Bảng hỏi 1)"},
            {"code": "0748", "name": "Dự án Ô tô 0748 (Bảng hỏi 2)"}
        ]
    })

# 3. API Danh sách ngày có dữ liệu
async def api_dates(request: Request):
    project = request.query_params.get("project", "0747")
    dates = get_available_dates(project)
    return JSONResponse({"project": project, "dates": dates})

# 4. API Phân tích Quota theo ngày & thành phố
async def api_quota(request: Request):
    project = request.query_params.get("project", "0747")
    date = request.query_params.get("date")
    city = request.query_params.get("city", "HCM")

    dates = get_available_dates(project)
    if not dates:
        return JSONResponse({"detail": "Chưa có dữ liệu quota cho dự án này"}, status_code=404)

    if not date:
        date = dates[0]

    record = get_upload_data(project, date)
    if not record:
        return JSONResponse({"detail": "Không tìm thấy dữ liệu cho ngày này"}, status_code=404)

    parsed_data = record["parsed_data"]
    result = QuotaEngine.analyze(parsed_data, target_city=city)
    
    result["total_achieved"] = record.get("total_achieved", 0)
    result["total_target"] = record.get("total_target", 0)
    result["file_name"] = record.get("file_name", "")
    result["quota_date"] = date
    result["project_code"] = project

    return JSONResponse(result)

# 5. API Upload file quota tự động nhận diện dự án và ngày
async def api_upload(request: Request):
    form = await request.form()
    file = form.get("file")

    if not file or not hasattr(file, "read"):
        return JSONResponse({"detail": "Vui lòng đính kèm file quota"}, status_code=400)

    filename = file.filename
    content = await file.read()

    # TỰ ĐỘNG NHẬN DIỆN MÃ DỰ ÁN VÀ NGÀY TỪ TÊN FILE
    auto_project, auto_date = extract_metadata_from_filename(filename)
    
    # Cho phép override nếu người dùng chỉ định rõ, nếu không dùng tự động hoàn toàn
    project = form.get("project")
    if not project or project == "auto":
        project = auto_project

    date_str = form.get("date")
    if not date_str or date_str == "auto":
        date_str = auto_date

    if os.environ.get("VERCEL"):
        save_dir = os.path.join("/tmp", "uploads", project)
    else:
        save_dir = os.path.join(BASE_DIR, "data", "uploads", project)
    os.makedirs(save_dir, exist_ok=True)
    saved_path = os.path.join(save_dir, f"{date_str}_{filename}")
    
    with open(saved_path, "wb") as f:
        f.write(content)

    try:
        parsed = QuotaParser.parse_xml_spreadsheet(saved_path)
        save_upload(project, date_str, filename, saved_path, parsed)
        return JSONResponse({
            "status": "success", 
            "project": project,
            "date": date_str,
            "filename": filename,
            "message": f"Hệ thống đã tự động nhận diện thành công: Dự án {project} • Ngày áp dụng {date_str}!"
        })
    except Exception as e:
        return JSONResponse({"detail": f"Lỗi đọc file: {str(e)}"}, status_code=400)

# 6. API Xuất file Excel
async def api_export_excel(request: Request):
    project = request.query_params.get("project", "0747")
    date = request.query_params.get("date")
    city = request.query_params.get("city", "HCM")

    dates = get_available_dates(project)
    if not date and dates:
        date = dates[0]

    record = get_upload_data(project, date)
    if not record:
        return Response("Dữ liệu không tồn tại", status_code=404)

    parsed_data = record["parsed_data"]
    analysis = QuotaEngine.analyze(parsed_data, target_city=city)
    excel_bytes = QuotaReporter.generate_excel(analysis, project, date)

    filename = f"Bao_Cao_Quota_{project}_{city}_{date}.xlsx"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
    return Response(excel_bytes, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)

# 7. API In ấn / Báo cáo HTML
async def api_export_html(request: Request):
    project = request.query_params.get("project", "0747")
    date = request.query_params.get("date")
    city = request.query_params.get("city", "HCM")

    dates = get_available_dates(project)
    if not date and dates:
        date = dates[0]

    record = get_upload_data(project, date)
    if not record:
        return Response("Dữ liệu không tồn tại", status_code=404)

    parsed_data = record["parsed_data"]
    analysis = QuotaEngine.analyze(parsed_data, target_city=city)
    html_content = QuotaReporter.generate_html(analysis, project, date)

    return HTMLResponse(html_content)

routes = [
    Route("/", homepage),
    Route("/api/projects", api_projects),
    Route("/api/dates", api_dates),
    Route("/api/quota", api_quota),
    Route("/api/upload", api_upload, methods=["POST"]),
    Route("/api/export/excel", api_export_excel),
    Route("/api/export/html", api_export_html),
    Mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static"),
]

bootstrap_sample_data()
app = Starlette(debug=True, routes=routes)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"=====================================================", flush=True)
    print(f"  VINAMR AUTOFIELD SERVER DANG CHAY TAI:", flush=True)
    print(f"  http://localhost:{port}", flush=True)
    print(f"  http://127.0.0.1:{port}", flush=True)
    print(f"=====================================================", flush=True)
    uvicorn.run(app, host=host, port=port, log_level="info")
