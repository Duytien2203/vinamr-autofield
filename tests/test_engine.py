import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.parser import QuotaParser
from core.engine import QuotaEngine

def test_engine_hcm_full_match():
    sample_path = os.path.join(os.path.dirname(__file__), "..", "data", "samples", "sample_quota_0747_20261106.xml")
    assert os.path.exists(sample_path)

    parsed = QuotaParser.parse_xml_spreadsheet(sample_path)
    result = QuotaEngine.analyze(parsed, target_city="HCM")

    # ==========================================
    # 1. KIỂM THỬ DỰ ĐỊNH MUA (INTENDERS)
    # ==========================================
    intenders = result["intenders"]
    assert intenders["count_models"] == 4
    assert intenders["total_remaining"] == 4

    exp_intenders = [
        ("VinFast VF3", "4/5", 1, "Nam", "4", "2", "—", "—"),
        ("Honda HR-V HEV", "2/3", 1, "Nam", "1", "—", "1", "—"),
        ("Mitsubishi Xforce", "4/5", 1, "Nam", "2", "1", "—", "—"),
        ("Honda CR-V", "4/5", 1, "Nam", "—", "—", "1", "—"),
    ]

    for idx, (exp_model, exp_q, exp_rem, exp_gender, exp_ft, exp_rp, exp_ad, exp_note) in enumerate(exp_intenders):
        item = intenders["items"][idx]
        assert item["model_name"] == exp_model
        assert item["quota_city_str"] == exp_q
        assert item["remaining_needed"] == exp_rem
        assert item["gender"] == exp_gender
        assert item["first_time_str"] == exp_ft
        assert item["replacement_str"] == exp_rp
        assert item["additional_str"] == exp_ad
        assert item["note"] == exp_note

    # ==========================================
    # 2. KIỂM THỬ ĐÃ SỞ HỮU (OWNERS)
    # ==========================================
    owners = result["owners"]
    assert owners["count_models"] == 22
    assert owners["total_remaining"] == 134

    exp_owners = [
        ("Toyota Vios", "8/11", 3, "Nam", "6", "4", "2", "—"),
        ("Toyota Raize", "2/7", 5, "Nam", "3", "6", "5", "—"),
        ("Kia Sonet", "4/7", 3, "Nam", "—", "5", "2", "—"),
        ("Honda HR-V", "2/11", 9, "Nam", "3", "7", "5", "—"),
        ("Honda HR-V HEV", "3/7", 4, "Nam", "3", "4", "3", "—"),
        ("Toyota Corolla Cross", "3/11", 7, "Nam", "2", "5", "5", "Giới hạn miền Nam"),
        ("Toyota Corolla Cross HEV", "4/7", 3, "Nam", "1", "—", "3", "—"),
        ("Mitsubishi Xforce", "3/11", 8, "Nam", "—", "5", "3", "—"),
        ("Honda CR-V", "2/11", 9, "Nam", "1", "7", "10", "—"),
        ("Honda CR-V HEV", "4/11", 7, "Nam / Nữ", "—", "12", "6", "—"),
        ("Ford Territory", "5/11", 5, "Nam", "—", "1", "4", "Đổi 1; Mua thêm 4"),
        ("Mitsubishi Destinator", "7/11", 4, "Nam", "—", "1", "3", "—"),
        ("Hyundai Santa Fe", "0/7", 7, "Nam / Nữ", "1", "10", "2", "—"),
        ("Ford Everest", "0/7", 7, "Nam / Nữ", "14", "15", "6", "—"),
        ("Hyundai Palisade", "0/7", 7, "Nam / Nữ", "17", "18", "7", "—"),
        ("Honda BR-V", "2/7", 5, "Nam", "6", "5", "2", "—"),
        ("VinFast MPV7", "6/7", 1, "Nam", "—", "2", "1", "—"),
        ("Ford Ranger XLS / XL / XLT", "0/8", 8, "Nam / Nữ", "18", "5", "12", "—"),
        ("Ford Ranger Sport / Wildtrak / Stormtrak", "0/8", 8, "Nam / Nữ", "26", "5", "14", "—"),
        ("Mitsubishi Triton GLX", "0/8", 8, "Nam / Nữ", "23", "5", "14", "—"),
        ("Mitsubishi Triton Athlete", "0/8", 8, "Nam / Nữ", "25", "6", "12", "—"),
        ("Toyota Hilux", "0/8", 8, "Nam / Nữ", "21", "6", "14", "—"),
    ]

    for idx, (exp_model, exp_q, exp_rem, exp_gender, exp_ft, exp_rp, exp_ad, exp_note) in enumerate(exp_owners):
        item = owners["items"][idx]
        assert item["model_name"] == exp_model, f"STT {idx+1}: {item['model_name']} != {exp_model}"
        assert item["quota_city_str"] == exp_q, f"STT {idx+1}: {item['quota_city_str']} != {exp_q}"
        assert item["remaining_needed"] == exp_rem, f"STT {idx+1}: {item['remaining_needed']} != {exp_rem}"
        assert item["gender"] == exp_gender, f"STT {idx+1}: {item['gender']} != {exp_gender}"
        assert item["first_time_str"] == exp_ft, f"STT {idx+1}: {item['first_time_str']} != {exp_ft}"
        assert item["replacement_str"] == exp_rp, f"STT {idx+1}: {item['replacement_str']} != {exp_rp}"
        assert item["additional_str"] == exp_ad, f"STT {idx+1}: {item['additional_str']} != {exp_ad}"
        assert item["note"] == exp_note, f"STT {idx+1}: {item['note']} != {exp_note}"

    print("🎉 TẤT CẢ 26 DÒNG XE VÀ ĐIỀU KIỆN (DỰ ĐỊNH 4 + ĐÃ SỞ HỮU 22) ĐẠT 100% CHÍNH XÁC!")

if __name__ == "__main__":
    test_engine_hcm_full_match()
