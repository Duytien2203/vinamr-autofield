print("Step 1: Imports start", flush=True)
import sys
import os
import asyncio
print("Step 2: sys, os, asyncio loaded", flush=True)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
print("Step 3: sys.path set", flush=True)

from starlette.requests import Request
print("Step 4: Request imported", flush=True)

import server
print("Step 5: server imported", flush=True)

def make_request(path: str, query_string: str = ""):
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "query_string": query_string.encode(),
        "headers": []
    }
    async def empty_receive():
        return {"type": "http.request", "body": b"", "more_body": False}
    return Request(scope, receive=empty_receive)

async def run_tests():
    print("Step 6: run_tests started", flush=True)
    req = make_request("/")
    resp = await server.homepage(req)
    assert resp.status_code == 200
    assert "VINAMR" in resp.body.decode("utf-8")
    print("   -> OK 200! Giao diện tải thành công.", flush=True)

    print("Step 7: checking api_projects", flush=True)
    req = make_request("/api/projects")
    resp = await server.api_projects(req)
    assert resp.status_code == 200
    import json
    data = json.loads(resp.body.decode("utf-8"))
    assert len(data["projects"]) == 2
    print(f"   -> OK! Có {len(data['projects'])} dự án.", flush=True)

    print("Step 8: checking api_dates", flush=True)
    req = make_request("/api/dates", "project=0747")
    resp = await server.api_dates(req)
    assert resp.status_code == 200
    dates = json.loads(resp.body.decode("utf-8"))["dates"]
    assert len(dates) >= 1
    print(f"   -> OK! Các ngày có dữ liệu: {dates}", flush=True)

    print("Step 9: checking api_quota", flush=True)
    req = make_request("/api/quota", "project=0747&city=HCM")
    resp = await server.api_quota(req)
    assert resp.status_code == 200
    quota_data = json.loads(resp.body.decode("utf-8"))
    assert quota_data["intenders"]["count_models"] == 4
    assert quota_data["intenders"]["total_remaining"] == 4
    assert quota_data["owners"]["count_models"] == 22
    assert quota_data["owners"]["total_remaining"] == 134
    print("   -> OK! Quota HCM chuẩn xác 100% (Dự định: 4, Đã sở hữu: 134).", flush=True)

    print("Step 10: checking api_export_excel", flush=True)
    req = make_request("/api/export/excel", "project=0747&city=HCM")
    resp = await server.api_export_excel(req)
    assert resp.status_code == 200
    assert len(resp.body) > 5000
    print(f"   -> OK! File Excel {len(resp.body)} bytes.", flush=True)

    print("Step 11: checking api_export_html", flush=True)
    req = make_request("/api/export/html", "project=0747&city=HCM")
    resp = await server.api_export_html(req)
    assert resp.status_code == 200
    assert "BÁO CÁO QUOTA TP.HCM" in resp.body.decode("utf-8")
    print("   -> OK! HTML báo cáo in ấn tạo thành công.", flush=True)

    print("\n🎉 TOÀN BỘ CÁC ENDPOINTS VÀ GIAO DIỆN MỚI HOẠT ĐỘNG HOÀN HẢO!", flush=True)

if __name__ == "__main__":
    asyncio.run(run_tests())
