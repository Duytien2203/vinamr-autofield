import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.parser import QuotaParser
from core.engine import QuotaEngine

sample_path = os.path.join(os.path.dirname(__file__), "..", "data", "samples", "sample_quota_0747_20261106.xml")
parsed = QuotaParser.parse_xml_spreadsheet(sample_path)
result = QuotaEngine.analyze(parsed, target_city="HCM")

print("STT | Mẫu xe | Quota HCM | Còn thiếu | Giới tính | SH lần đầu | Đổi xe | Mua thêm | Lưu ý")
print("-" * 90)
for idx, item in enumerate(result["owners"]["items"], start=1):
    print(f"{idx:2d} | {item['model_name']:<30} | {item['quota_city_str']:<9} | {item['remaining_needed']:<9} | {item['gender']:<9} | {item['first_time_str']:<10} | {item['replacement_str']:<6} | {item['additional_str']:<8} | {item['note']}")
print("-" * 90)
print("Tổng còn thiếu:", result["owners"]["total_remaining"])
