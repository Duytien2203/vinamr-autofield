"""
Core Engine: Bộ máy tính toán và phân tích quota đa tầng cho dự án ô tô.
Áp dụng đầy đủ 6 quy tắc khống chế: Toàn quốc, Phân khúc, Vùng miền, Giới tính, Hình thức mua xe.
"""

from typing import Dict, List, Any, Optional

class QuotaEngine:
    
    REGION_NAME_MAP = {
        "Bắc": "miền Bắc",
        "Trung": "miền Trung",
        "Nam": "miền Nam"
    }

    CITY_REGION_MAP = {
        "Hà Nội": "Bắc",
        "Hải Phòng": "Bắc",
        "Nghệ An": "Trung",
        "Đà Nẵng": "Trung",
        "HCM": "Nam",
        "Cần Thơ": "Nam",
    }

    @classmethod
    def get_region_for_city(cls, city: str) -> str:
        return cls.CITY_REGION_MAP.get(city, "Nam")

    @classmethod
    def _compute_purchase_rem(cls, p_dict: Dict[str, Any], status: str, seg_p_dict: Optional[Dict[str, Any]]) -> int:
        """
        Tính số lượng còn trống của một hình thức (Lần đầu, Đổi, Mua thêm).
        rem = min(status_rem, model_total_rem, segment_total_rem).
        """
        m_tot_ach, m_tot_tgt, m_tot_rem = p_dict["total"]
        st_ach, st_tgt, st_rem = p_dict[status]
        
        # Nếu model status đã hết
        if st_tgt == 0 or st_rem == 0:
            return 0
        
        rem = st_rem
        
        # Cắt theo tổng toàn mẫu của hình thức đó
        if m_tot_tgt > 0:
            rem = min(rem, m_tot_rem)
            
        # Cắt theo tổng phân khúc của hình thức đó
        if seg_p_dict:
            seg_tot_ach, seg_tot_tgt, seg_tot_rem = seg_p_dict.get("total", (0, 0, 999))
            if seg_tot_tgt > 0:
                rem = min(rem, seg_tot_rem)
                
        return max(0, rem)

    @classmethod
    def analyze(cls, parsed_data: Dict[str, Any], target_city: str = "HCM") -> Dict[str, Any]:
        """
        Phân tích quota theo thành phố chỉ định (mặc định HCM).
        Trả về kết quả cho cả 2 nhóm:
        - intenders (Dự định mua)
        - owners (Đã sở hữu)
        cùng danh sách lưu ý khống chế.
        """
        rows = parsed_data.get("rows", [])
        target_region = cls.get_region_for_city(target_city)
        region_field = "region_south" if target_region == "Nam" else ("region_north" if target_region == "Bắc" else "region_central")
        region_display = cls.REGION_NAME_MAP.get(target_region, f"miền {target_region}")

        # 1. Thu thập thông tin cấp Phân khúc (Segment totals)
        segment_totals: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            if r.get("is_segment_total"):
                seg_name = r.get("segment", "")
                segment_totals[seg_name] = r

        # 2. Danh sách lưu ý khống chế tổng quát
        general_notes: List[str] = []
        
        # Kiểm tra các phân khúc đã đủ quota
        for seg_name, s_row in segment_totals.items():
            # Kiểm tra phân khúc Dự định
            intender_ach, intender_tgt, _ = s_row["status_intender"]
            if intender_tgt > 0 and intender_ach >= intender_tgt:
                general_notes.append(
                    f"• {seg_name}: quota Dự định cấp phân khúc đã đạt {intender_ach}/{intender_tgt}; "
                    f"không tuyển các dòng thuộc phân khúc này vào nhóm Dự định."
                )
            # Kiểm tra phân khúc Đã sở hữu
            owner_ach, owner_tgt, _ = s_row["status_owner"]
            if owner_tgt > 0 and owner_ach >= owner_tgt:
                general_notes.append(
                    f"• {seg_name}: quota Đã sở hữu cấp phân khúc đã đạt {owner_ach}/{owner_tgt}; "
                    f"không tuyển các dòng thuộc phân khúc này vào nhóm Đã sở hữu."
                )

        intender_list: List[Dict[str, Any]] = []
        owner_list: List[Dict[str, Any]] = []

        # Các dòng xe bị loại trừ hoặc đủ toàn quốc
        fully_completed_models: List[str] = []
        zero_quota_models: List[str] = []

        for r in rows:
            if not r.get("is_model"):
                continue

            model_name = r.get("model_name", "")
            seg_name = r.get("segment", "")
            seg_row = segment_totals.get(seg_name, {})

            tot_ach, tot_tgt, tot_rem = r["total"]
            
            # Quy tắc: Xe có TOTAL 0/0
            if tot_tgt == 0:
                zero_quota_models.append(model_name)
                continue

            # Quy tắc: Xe đã đủ TOTAL
            if tot_ach >= tot_tgt:
                fully_completed_models.append(f"{model_name} ({tot_ach}/{tot_tgt})")
                continue

            # Lấy thông tin vùng miền của xe này
            reg_ach, reg_tgt, reg_rem = r.get(region_field, (0, 0, 0))
            
            # Giới tính của xe này (kiểm tra cả trần model và trần phân khúc)
            m_ach, m_tgt, m_rem = r["gender_male"]
            f_ach, f_tgt, f_rem = r["gender_female"]
            
            seg_f_ach, seg_f_tgt, seg_f_rem = seg_row.get("gender_female", (0, 0, 1)) if seg_row else (0, 0, 1)
            seg_m_ach, seg_m_tgt, seg_m_rem = seg_row.get("gender_male", (0, 0, 1)) if seg_row else (0, 0, 1)

            female_blocked = (f_tgt > 0 and f_ach >= f_tgt) or (seg_f_tgt > 0 and seg_f_ach >= seg_f_tgt)
            male_blocked = (m_tgt > 0 and m_ach >= m_tgt) or (seg_m_tgt > 0 and seg_m_ach >= seg_m_tgt)

            if female_blocked and not male_blocked and m_rem > 0:
                gender_str = "Nam"
            elif male_blocked and not female_blocked and f_rem > 0:
                gender_str = "Nữ"
            else:
                gender_str = "Nam / Nữ"

            seg_pt = seg_row.get("purchase_types", {}) if seg_row else {}

            # ==========================================
            # A. XỬ LÝ NHÓM: DỰ ĐỊNH MUA (INTENDERS)
            # ==========================================
            intender_model_ach, intender_model_tgt, intender_model_rem = r["status_intender"]
            city_intender_ach, city_intender_tgt, city_intender_rem = r["cities"].get(target_city, {}).get("intender", (0, 0, 0))

            seg_intender_ach, seg_intender_tgt, seg_intender_rem = seg_row.get("status_intender", (0, 0, 0)) if seg_row else (0, 0, 0)
            seg_intender_locked = (seg_intender_tgt > 0 and seg_intender_ach >= seg_intender_tgt)

            if not seg_intender_locked and intender_model_rem > 0 and city_intender_tgt > 0 and city_intender_rem > 0:
                ft_rem = cls._compute_purchase_rem(r["purchase_types"]["first_time"], "intender", seg_pt.get("first_time"))
                rp_rem = cls._compute_purchase_rem(r["purchase_types"]["replacement"], "intender", seg_pt.get("replacement"))
                ad_rem = cls._compute_purchase_rem(r["purchase_types"]["additional"], "intender", seg_pt.get("additional"))

                remaining_needed = city_intender_rem
                note_items = []

                if reg_tgt > 0 and reg_rem < remaining_needed:
                    remaining_needed = reg_rem
                    note_items.append(f"Giới hạn {region_display}")

                total_purchase_capacity = ft_rem + rp_rem + ad_rem
                if total_purchase_capacity < remaining_needed:
                    remaining_needed = total_purchase_capacity
                    p_details = []
                    if ft_rem > 0: p_details.append(f"Lần đầu {ft_rem}")
                    if rp_rem > 0: p_details.append(f"Đổi {rp_rem}")
                    if ad_rem > 0: p_details.append(f"Mua thêm {ad_rem}")
                    if p_details:
                        note_items.append("; ".join(p_details))

                if remaining_needed > 0:
                    intender_list.append({
                        "model_name": cls._clean_model_display(model_name),
                        "raw_model_name": model_name,
                        "segment": seg_name,
                        "quota_city_str": f"{city_intender_ach}/{city_intender_tgt}",
                        "remaining_needed": remaining_needed,
                        "gender": gender_str,
                        "first_time_str": str(ft_rem) if ft_rem > 0 else "—",
                        "replacement_str": str(rp_rem) if rp_rem > 0 else "—",
                        "additional_str": str(ad_rem) if ad_rem > 0 else "—",
                        "note": "; ".join(note_items) if note_items else "—",
                    })

            # ==========================================
            # B. XỬ LÝ NHÓM: ĐÃ SỞ HỮU (OWNERS)
            # ==========================================
            owner_model_ach, owner_model_tgt, owner_model_rem = r["status_owner"]
            city_owner_ach, city_owner_tgt, city_owner_rem = r["cities"].get(target_city, {}).get("owner", (0, 0, 0))

            seg_owner_ach, seg_owner_tgt, seg_owner_rem = seg_row.get("status_owner", (0, 0, 0)) if seg_row else (0, 0, 0)
            seg_owner_locked = (seg_owner_tgt > 0 and seg_owner_ach >= seg_owner_tgt)

            if not seg_owner_locked and owner_model_rem > 0 and city_owner_tgt > 0 and city_owner_rem > 0:
                ft_rem = cls._compute_purchase_rem(r["purchase_types"]["first_time"], "owner", seg_pt.get("first_time"))
                rp_rem = cls._compute_purchase_rem(r["purchase_types"]["replacement"], "owner", seg_pt.get("replacement"))
                ad_rem = cls._compute_purchase_rem(r["purchase_types"]["additional"], "owner", seg_pt.get("additional"))

                remaining_needed = city_owner_rem
                note_items = []

                if reg_tgt > 0 and reg_rem < remaining_needed:
                    remaining_needed = reg_rem
                    note_items.append(f"Giới hạn {region_display}")

                total_purchase_capacity = ft_rem + rp_rem + ad_rem
                if total_purchase_capacity < remaining_needed:
                    remaining_needed = total_purchase_capacity
                    p_details = []
                    if ft_rem > 0: p_details.append(f"Lần đầu {ft_rem}")
                    if rp_rem > 0: p_details.append(f"Đổi {rp_rem}")
                    if ad_rem > 0: p_details.append(f"Mua thêm {ad_rem}")
                    if p_details:
                        note_items.append("; ".join(p_details))

                if remaining_needed > 0:
                    owner_list.append({
                        "model_name": cls._clean_model_display(model_name),
                        "raw_model_name": model_name,
                        "segment": seg_name,
                        "quota_city_str": f"{city_owner_ach}/{city_owner_tgt}",
                        "remaining_needed": remaining_needed,
                        "gender": gender_str,
                        "first_time_str": str(ft_rem) if ft_rem > 0 else "—",
                        "replacement_str": str(rp_rem) if rp_rem > 0 else "—",
                        "additional_str": str(ad_rem) if ad_rem > 0 else "—",
                        "note": "; ".join(note_items) if note_items else "—",
                    })

        # Bổ sung các lưu ý xe đủ và 0/0 vào general_notes
        if fully_completed_models:
            general_notes.append(f"• Các dòng xe đã đủ TOTAL: {', '.join(fully_completed_models)}; không tuyển thêm.")
        if zero_quota_models:
            general_notes.append(f"• Các dòng TOTAL 0/0: {', '.join(zero_quota_models[:5])}... không được tuyển.")

        return {
            "city": target_city,
            "region": target_region,
            "intenders": {
                "items": intender_list,
                "total_remaining": sum(x["remaining_needed"] for x in intender_list),
                "count_models": len(intender_list)
            },
            "owners": {
                "items": owner_list,
                "total_remaining": sum(x["remaining_needed"] for x in owner_list),
                "count_models": len(owner_list)
            },
            "general_notes": general_notes
        }

    @classmethod
    def _clean_model_display(cls, raw_name: str) -> str:
        """
        Chuẩn hóa tên xe hiển thị đẹp mắt theo chuẩn báo cáo.
        VD: 'VINFAST - VF-3' -> 'VinFast VF3', 'HONDA - HR-V - HEV' -> 'Honda HR-V HEV'.
        """
        raw = raw_name.strip()
        exact_map = {
            "VINFAST - VF-3": "VinFast VF3",
            "HONDA - CITY": "Honda City",
            "TOYOTA - VIOS": "Toyota Vios",
            "TOYOTA - RAIZE": "Toyota Raize",
            "KIA - SONET": "Kia Sonet",
            "HONDA - HR-V": "Honda HR-V",
            "HONDA - HR-V - HEV": "Honda HR-V HEV",
            "TOYOTA - COROLLA CROSS": "Toyota Corolla Cross",
            "TOYOTA - COROLLA CROSS - HEV": "Toyota Corolla Cross HEV",
            "TOYOTA - YARIS CROSS": "Toyota Yaris Cross",
            "TOYOTA - YARIS CROSS - HEV": "Toyota Yaris Cross HEV",
            "MITSUBISHI - XFORCE": "Mitsubishi Xforce",
            "HONDA - CR-V": "Honda CR-V",
            "HONDA - CR-V - HEV": "Honda CR-V HEV",
            "MAZDA - CX-5 2.0": "Mazda CX-5 2.0",
            "HYUNDAI - TUCSON": "Hyundai Tucson",
            "HYUNDAI - TUCSON - HEV": "Hyundai Tucson HEV",
            "FORD - TERRITORY": "Ford Territory",
            "MITSUBISHI - DESTINATOR": "Mitsubishi Destinator",
            "HYUNDAI - SANTAFE": "Hyundai Santa Fe",
            "FORD - EVEREST": "Ford Everest",
            "HYUNDAI - PALISADE": "Hyundai Palisade",
            "HONDA - BR-V": "Honda BR-V",
            "TOYOTA - VELOZ CROSS": "Toyota Veloz Cross",
            "MITSUBISHI - XPANDER": "Mitsubishi Xpander",
            "VINFAST - MPV7": "VinFast MPV7",
            "FORD - RANGER - XLS, XL, XLT": "Ford Ranger XLS / XL / XLT",
            "FORD - RANGER - Sport, wild track, storm track": "Ford Ranger Sport / Wildtrak / Stormtrak",
            "MITSUBISHI - TRITON - GLX": "Mitsubishi Triton GLX",
            "MITSUBISHI - TRITON - Athelete": "Mitsubishi Triton Athlete",
            "TOYOTA - HILUX": "Toyota Hilux"
        }
        if raw in exact_map:
            return exact_map[raw]

        name = raw.replace(" - ", " ").replace("-", " ")
        parts = [p.capitalize() if p.lower() not in ["hev", "mpv7", "glx", "xls", "xl", "xlt", "cr-v", "hr-v", "br-v", "cx-5", "vf3"] else p.upper() for p in name.split()]
        return " ".join(parts)
