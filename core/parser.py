"""
Module phân tích cú pháp (Parser) cho file Quota Nghiên cứu Thị trường Ô tô.
Hỗ trợ định dạng SpreadsheetML XML (Excel 2003 XML) và file Excel .xlsx.
"""

import os
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Any

def parse_cell_ratio(val_str: Optional[str]) -> Tuple[int, int, int]:
    """
    Phân tích chuỗi tỷ lệ 'Đạt / Mục tiêu' (VD: '4 / 5', '1167 / 2190').
    Trả về tuple: (achieved, target, remaining).
    """
    if not val_str or not isinstance(val_str, str):
        return (0, 0, 0)
    
    val_str = val_str.strip()
    match = re.match(r"^(\d+)\s*/\s*(\d+)$", val_str)
    if match:
        achieved = int(match.group(1))
        target = int(match.group(2))
        remaining = max(0, target - achieved)
        return (achieved, target, remaining)
    
    # Trường hợp số đơn lẻ
    if val_str.isdigit():
        num = int(val_str)
        return (num, num, 0)
    
    return (0, 0, 0)

def extract_metadata_from_filename(filename: str) -> Tuple[str, str]:
    """
    Tự động nhận diện mã dự án (0747/0748) và ngày áp dụng quota (YYYY-MM-DD) từ tên file.
    VD: '[MAIN] - 0747 - CP2026_2026_06_11_14_00' -> ('0747', '2026-11-06')
    """
    fn = os.path.basename(filename)
    
    # 1. Nhận diện dự án (0747 hoặc 0748)
    if "0748" in fn or "748" in fn:
        project_code = "0748"
    elif "0747" in fn or "747" in fn:
        project_code = "0747"
    else:
        project_code = "0747"
        
    # 2. Nhận diện ngày áp dụng
    # Định dạng chuẩn công ty: YYYY_DD_MM_HH_MM (VD: 2026_06_11_14_00 = ngày 06 tháng 11 năm 2026)
    m = re.search(r"(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})", fn)
    if m:
        year, p1, p2, hh, mm = m.groups()
        # Theo chuẩn công ty trong mẫu: 2026_06_11 là ngày 06/11
        if int(p2) <= 12 and int(p1) <= 31:
            day, month = p1, p2
        elif int(p1) <= 12 and int(p2) > 12:
            month, day = p1, p2
        else:
            day, month = p1, p2
        return (project_code, f"{year}-{month.zfill(2)}-{day.zfill(2)}")
        
    # Định dạng chuẩn ISO YYYY-MM-DD
    m_iso = re.search(r"(\d{4})-(\d{2})-(\d{2})", fn)
    if m_iso:
        year, month, day = m_iso.groups()
        return (project_code, f"{year}-{month.zfill(2)}-{day.zfill(2)}")

    # Định dạng YYYY_DD_MM
    m2 = re.search(r"(\d{4})_(\d{2})_(\d{2})", fn)
    if m2:
        year, p1, p2 = m2.groups()
        if int(p2) <= 12 and int(p1) <= 31:
            day, month = p1, p2
        elif int(p1) <= 12 and int(p2) > 12:
            month, day = p1, p2
        else:
            day, month = p1, p2
        return (project_code, f"{year}-{month.zfill(2)}-{day.zfill(2)}")
        
    # Định dạng compact YYYYMMDD
    m3 = re.search(r"(\d{4})(\d{2})(\d{2})", fn)
    if m3:
        year, month, day = m3.groups()
        return (project_code, f"{year}-{month}-{day}")
        
    # Mặc định lấy ngày hiện tại
    from datetime import datetime
    return (project_code, datetime.now().strftime("%Y-%m-%d"))

class QuotaParser:
    """
    Parser chuyên dụng đọc bảng Quota ma trận ô tô.
    """
    
    CITY_REGION_MAP = {
        "Hà Nội": "Bắc",
        "Hải Phòng": "Bắc",
        "Nghệ An": "Trung",
        "Đà Nẵng": "Trung",
        "HCM": "Nam",
        "Cần Thơ": "Nam",
    }
    
    CITY_COL_KEY_MAP = {
        "Hà Nội": "Hà Nội",
        "Hải Phòng": "Hải Phòng",
        "Nghệ An": "Nghệ An",
        "Đà Nẵng": "Đà Nẵng",
        "HCM": "HCM",
        "Cần Thơ": "Cần Thơ",
    }
    
    @classmethod
    def parse_xml_spreadsheet(cls, file_path_or_content: str) -> Dict[str, Any]:
        """
        Đọc file XML SpreadsheetML.
        """
        if os.path.exists(file_path_or_content):
            tree = ET.parse(file_path_or_content)
            root = tree.getroot()
        else:
            root = ET.fromstring(file_path_or_content)
            
        # Namespace của SpreadsheetML
        ns = {
            'ss': 'urn:schemas-microsoft-com:office:spreadsheet',
            'o': 'urn:schemas-microsoft-com:office:office',
            'x': 'urn:schemas-microsoft-com:office:excel'
        }
        
        worksheet = root.find('.//ss:Worksheet', ns)
        if worksheet is None:
            raise ValueError("Không tìm thấy Worksheet trong file XML!")
            
        table = worksheet.find('ss:Table', ns)
        if table is None:
            raise ValueError("Không tìm thấy Table trong Worksheet!")
            
        rows_data: List[List[str]] = []
        for row in table.findall('ss:Row', ns):
            current_row: List[str] = []
            col_idx = 0
            for cell in row.findall('ss:Cell', ns):
                # Xử lý thuộc tính ss:Index nếu có ô bị nhảy cóc
                index_attr = cell.get(f"{{{ns['ss']}}}Index")
                if index_attr:
                    target_col = int(index_attr) - 1
                    while col_idx < target_col:
                        current_row.append("")
                        col_idx += 1
                        
                data_elem = cell.find('ss:Data', ns)
                text = data_elem.text if data_elem is not None and data_elem.text is not None else ""
                current_row.append(text.strip())
                col_idx += 1
            rows_data.append(current_row)
            
        if not rows_data:
            raise ValueError("Bảng không có dữ liệu!")
            
        headers = rows_data[0]
        
        # Tìm chỉ số các cột quan trọng
        col_indices = {}
        for idx, h in enumerate(headers):
            h_clean = h.strip()
            col_indices[h_clean] = idx

        parsed_rows = []
        for r_idx in range(1, len(rows_data)):
            row = rows_data[r_idx]
            if not row or not any(row):
                continue
            
            def get_val(col_name: str) -> str:
                idx = col_indices.get(col_name)
                if idx is not None and idx < len(row):
                    return row[idx]
                return ""
                
            level_1 = get_val("Level 1")
            level_2 = get_val("Level 2")
            
            row_dict = {
                "row_index": r_idx,
                "level_1": level_1,
                "level_2": level_2,
                "is_total": "[TOTALR]" in level_1 or level_1 == "[TOTALR] TOTAL",
                "is_segment_total": "[TOTALS]" in level_2 or level_2 == "[TOTALS] TOTAL SEG",
                "is_model": "[QTMODEL]" in level_2,
                "segment": level_1.replace("[SEG]", "").strip() if "[SEG]" in level_1 else level_1,
                "model_name": level_2.replace("[QTMODEL]", "").strip() if "[QTMODEL]" in level_2 else level_2,
                
                # Toàn bộ mẫu
                "total": parse_cell_ratio(get_val("TOTALC / TOTAL")),
                "gender_male": parse_cell_ratio(get_val("QTGENDER / Nam")),
                "gender_female": parse_cell_ratio(get_val("QTGENDER / Nữ")),
                
                # Vùng miền
                "region_north": parse_cell_ratio(get_val("QTVM / Bắc")),
                "region_central": parse_cell_ratio(get_val("QTVM / Trung")),
                "region_south": parse_cell_ratio(get_val("QTVM / Nam")),
                
                # Trạng thái sở hữu tổng thể
                "status_owner": parse_cell_ratio(get_val("QTSHDD / Người sở hữu")),
                "status_intender": parse_cell_ratio(get_val("QTSHDD / Người dự định")),
                
                # Chi tiết theo Thành phố
                "cities": {
                    "Hà Nội": {
                        "total": parse_cell_ratio(get_val("QTCITY / Hà Nội / QTTOTALCITY / TOTAL")),
                        "owner": parse_cell_ratio(get_val("QTCITY / Hà Nội / QTSHDDCITY / Người sở hữu")),
                        "intender": parse_cell_ratio(get_val("QTCITY / Hà Nội / QTSHDDCITY / Người dự định")),
                    },
                    "Hải Phòng": {
                        "total": parse_cell_ratio(get_val("QTCITY / Hải Phòng / QTTOTALCITY / TOTAL")),
                        "owner": parse_cell_ratio(get_val("QTCITY / Hải Phòng / QTSHDDCITY / Người sở hữu")),
                        "intender": parse_cell_ratio(get_val("QTCITY / Hải Phòng / QTSHDDCITY / Người dự định")),
                    },
                    "Nghệ An": {
                        "total": parse_cell_ratio(get_val("QTCITY / Nghệ An / QTTOTALCITY / TOTAL")),
                        "owner": parse_cell_ratio(get_val("QTCITY / Nghệ An / QTSHDDCITY / Người sở hữu")),
                        "intender": parse_cell_ratio(get_val("QTCITY / Nghệ An / QTSHDDCITY / Người dự định")),
                    },
                    "Đà Nẵng": {
                        "total": parse_cell_ratio(get_val("QTCITY / Đà Nẵng / QTTOTALCITY / TOTAL")),
                        "owner": parse_cell_ratio(get_val("QTCITY / Đà Nẵng / QTSHDDCITY / Người sở hữu")),
                        "intender": parse_cell_ratio(get_val("QTCITY / Đà Nẵng / QTSHDDCITY / Người dự định")),
                    },
                    "HCM": {
                        "total": parse_cell_ratio(get_val("QTCITY / HCM / QTTOTALCITY / TOTAL")),
                        "owner": parse_cell_ratio(get_val("QTCITY / HCM / QTSHDDCITY / Người sở hữu")),
                        "intender": parse_cell_ratio(get_val("QTCITY / HCM / QTSHDDCITY / Người dự định")),
                    },
                    "Cần Thơ": {
                        "total": parse_cell_ratio(get_val("QTCITY / Cần Thơ / QTTOTALCITY / TOTAL")),
                        "owner": parse_cell_ratio(get_val("QTCITY / Cần Thơ / QTSHDDCITY / Người sở hữu")),
                        "intender": parse_cell_ratio(get_val("QTCITY / Cần Thơ / QTSHDDCITY / Người dự định")),
                    },
                },
                
                # Chi tiết theo Hình thức sở hữu / mua xe (QTTTSH)
                "purchase_types": {
                    "first_time": {
                        "total": parse_cell_ratio(get_val("QTTTSH / Sở hữu lần đầu / QTTOTAL / TOTAL")),
                        "owner": parse_cell_ratio(get_val("QTTTSH / Sở hữu lần đầu / QTSHDD2 / Người sở hữu")),
                        "intender": parse_cell_ratio(get_val("QTTTSH / Sở hữu lần đầu / QTSHDD2 / Người dự định")),
                    },
                    "replacement": {
                        "total": parse_cell_ratio(get_val("QTTTSH / Đổi xe/thay xe / QTTOTAL / TOTAL")),
                        "owner": parse_cell_ratio(get_val("QTTTSH / Đổi xe/thay xe / QTSHDD2 / Người sở hữu")),
                        "intender": parse_cell_ratio(get_val("QTTTSH / Đổi xe/thay xe / QTSHDD2 / Người dự định")),
                    },
                    "additional": {
                        "total": parse_cell_ratio(get_val("QTTTSH / Mua thêm xe / QTTOTAL / TOTAL")),
                        "owner": parse_cell_ratio(get_val("QTTTSH / Mua thêm xe / QTSHDD2 / Người sở hữu")),
                        "intender": parse_cell_ratio(get_val("QTTTSH / Mua thêm xe / QTSHDD2 / Người dự định")),
                    },
                }
            }
            parsed_rows.append(row_dict)
            
        return {
            "headers": headers,
            "rows": parsed_rows
        }
