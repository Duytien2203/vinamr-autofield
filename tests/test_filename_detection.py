import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.parser import extract_metadata_from_filename

def test_metadata_extraction():
    test_cases = [
        ("[MAIN] - 0747 - CP2026_2026_06_11_14_00.xml", "0747", "2026-11-06"),
        ("[MAIN] - 0748 - CP2026_2026_06_11_14_00.xlsx", "0748", "2026-11-06"),
        ("[MAIN] - 748 - CP2026_2026_15_11_09_30.xml", "0748", "2026-11-15"),
        ("0747_2026_25_11_12_00.xml", "0747", "2026-11-25"),
        ("Quota_0748_2026-11-06.xml", "0748", "2026-11-06"),
    ]

    for fn, exp_proj, exp_date in test_cases:
        proj, date_str = extract_metadata_from_filename(fn)
        print(f"File: {fn:<45} -> Dự án: {proj} | Ngày: {date_str}")
        assert proj == exp_proj, f"Dự án không khớp: {proj} != {exp_proj}"
        assert date_str == exp_date, f"Ngày không khớp: {date_str} != {exp_date}"

    print("\n✅ TẤT CẢ TEST CASES TỰ ĐỘNG NHẬN DIỆN DỰ ÁN VÀ NGÀY TỪ TÊN FILE ĐỀU CHUẨN XÁC 100%!")

if __name__ == "__main__":
    test_metadata_extraction()
