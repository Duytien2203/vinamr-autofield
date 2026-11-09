"""
Module xuất báo cáo tuyển dụng ô tô:
- File Excel (.xlsx) với định dạng bảng biểu, màu sắc chuẩn nhận diện
- Báo cáo HTML in ấn (Printable HTML / PDF layout) chuẩn như bản PDF của dự án.
"""

import io
import mimetypes

# Khắc phục quyền đọc Registry trên Windows sandbox
if hasattr(mimetypes, "_mimetypes_read_windows_registry"):
    mimetypes._mimetypes_read_windows_registry = lambda add_type: None

from typing import Dict, Any, List
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

class QuotaReporter:

    @classmethod
    def generate_excel(cls, analysis_data: Dict[str, Any], project_code: str, quota_date: str) -> bytes:
        """
        Tạo file Excel (.xlsx) gồm 2 sheet: 'DỰ ĐỊNH MUA' và 'ĐÃ SỞ HỮU'.
        """
        wb = Workbook()
        wb.remove(wb.active) # Xóa sheet mặc định
        
        city = analysis_data.get("city", "HCM")
        intenders = analysis_data.get("intenders", {})
        owners = analysis_data.get("owners", {})
        general_notes = analysis_data.get("general_notes", [])
        
        # Styles dùng chung
        font_title = Font(name="Segoe UI", size=14, bold=True, color="1B4D68")
        font_sub = Font(name="Segoe UI", size=10, italic=True, color="555555")
        font_header = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        font_data = Font(name="Segoe UI", size=9, color="000000")
        font_total = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        font_notes_title = Font(name="Segoe UI", size=10, bold=True, color="C0392B")
        font_note_item = Font(name="Segoe UI", size=9, color="333333")
        
        fill_header = PatternFill(start_color="1B4D68", end_color="1B4D68", fill_type="solid")
        fill_total = PatternFill(start_color="0F2C3D", end_color="0F2C3D", fill_type="solid")
        fill_zebra = PatternFill(start_color="F9FAFB", end_color="F9FAFB", fill_type="solid")
        
        thin_border = Border(
            left=Side(style='thin', color="DDDDDD"),
            right=Side(style='thin', color="DDDDDD"),
            top=Side(style='thin', color="DDDDDD"),
            bottom=Side(style='thin', color="DDDDDD")
        )
        
        align_center = Alignment(horizontal="center", vertical="center")
        align_left = Alignment(horizontal="left", vertical="center")
        align_right = Alignment(horizontal="right", vertical="center")

        def build_sheet(sheet_title: str, items: List[Dict[str, Any]], total_needed: int, is_intender: bool):
            ws = wb.create_sheet(title=sheet_title)
            ws.views.sheetView[0].showGridLines = True
            
            # 1. Header Báo cáo
            ws.merge_cells("A1:I1")
            ws["A1"] = f"BÁO CÁO QUOTA TP.{city} | {sheet_title.upper()}"
            ws["A1"].font = font_title
            ws["A1"].alignment = align_left
            
            ws.merge_cells("A2:I2")
            ws["A2"] = f"Dự án {project_code} | Ngày {quota_date} | {len(items)} dòng xe còn quota | {total_needed} đáp viên còn thiếu"
            ws["A2"].font = font_sub
            ws["A2"].alignment = align_left
            
            ws.append([]) # Row 3 trống
            
            # 2. Tiêu đề các cột
            headers = [
                "STT", "Mẫu xe", f"Quota {city}\n(Đạt/Mục tiêu)", "Còn thiếu", 
                "Giới tính", "Sở hữu\nlần đầu¹", "Đổi xe /\nThay xe¹", "Mua\nthêm xe¹", "Lưu ý"
            ]
            ws.append(headers)
            header_row_idx = 4
            ws.row_dimensions[header_row_idx].height = 28
            
            for col_idx in range(1, len(headers) + 1):
                cell = ws.cell(row=header_row_idx, column=col_idx)
                cell.font = font_header
                cell.fill = fill_header
                cell.alignment = align_center
                cell.border = thin_border

            # 3. Dữ liệu các dòng xe
            current_row = 5
            for idx, it in enumerate(items, start=1):
                ws.row_dimensions[current_row].height = 22
                row_vals = [
                    idx,
                    it["model_name"],
                    it["quota_city_str"],
                    it["remaining_needed"],
                    it["gender"],
                    it["first_time_str"],
                    it["replacement_str"],
                    it["additional_str"],
                    it["note"]
                ]
                ws.append(row_vals)
                
                # Định dạng ô
                for c_idx in range(1, len(row_vals) + 1):
                    cell = ws.cell(row=current_row, column=c_idx)
                    cell.font = font_data
                    cell.border = thin_border
                    if current_row % 2 == 0:
                        cell.fill = fill_zebra
                    
                    if c_idx == 2:
                        cell.alignment = align_left
                    elif c_idx == 9:
                        cell.alignment = align_left
                    else:
                        cell.alignment = align_center
                        
                current_row += 1
                
            # 4. Hàng TỔNG
            ws.row_dimensions[current_row].height = 24
            ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=3)
            ws.cell(row=current_row, column=1, value="TỔNG").alignment = align_center
            ws.cell(row=current_row, column=4, value=total_needed).alignment = align_center
            
            for c_idx in range(1, 10):
                cell = ws.cell(row=current_row, column=c_idx)
                cell.font = font_total
                cell.fill = fill_total
                cell.border = thin_border
                
            current_row += 2
            
            # 5. Ghi chú chân trang & Lưu ý khống chế
            ws.cell(row=current_row, column=1, value="¹ Ba cột hình thức thể hiện quota còn trống của nhóm tại cấp toàn mẫu sau khi đối chiếu quota hình thức tổng và phân khúc; không phải quota riêng thành phố.").font = font_sub
            current_row += 1
            ws.cell(row=current_row, column=1, value="“Còn thiếu” là mức tuyển theo từng dòng xe sau khi kiểm tra TOTAL, Vùng miền, Thành phố, Tình trạng sở hữu, Giới tính và Hình thức mua xe.").font = font_sub
            current_row += 2
            
            if is_intender:
                ws.cell(row=current_row, column=1, value="LƯU Ý QUOTA KHỐNG CHẾ:").font = font_notes_title
                current_row += 1
                for gn in general_notes:
                    ws.cell(row=current_row, column=1, value=gn).font = font_note_item
                    current_row += 1
                    
            # Tối ưu độ rộng cột
            col_widths = [8, 32, 16, 12, 14, 14, 14, 14, 25]
            for i, w in enumerate(col_widths, start=1):
                col_letter = get_column_letter(i)
                ws.column_dimensions[col_letter].width = w

        # Tạo Sheet 1 và Sheet 2
        build_sheet("Dự định mua", intenders.get("items", []), intenders.get("total_remaining", 0), is_intender=True)
        build_sheet("Đã sở hữu", owners.get("items", []), owners.get("total_remaining", 0), is_intender=False)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    @classmethod
    def generate_html(cls, analysis_data: Dict[str, Any], project_code: str, quota_date: str) -> str:
        """
        Tạo báo cáo dạng HTML chuẩn in ấn trang nhã giống hệt file PDF.
        """
        city = analysis_data.get("city", "HCM")
        intenders = analysis_data.get("intenders", {})
        owners = analysis_data.get("owners", {})
        general_notes = analysis_data.get("general_notes", [])

        def render_table_rows(items: List[Dict[str, Any]]) -> str:
            rows_html = []
            for idx, it in enumerate(items, start=1):
                bg_class = "bg-gray-50" if idx % 2 == 0 else "bg-white"
                note_badge = ""
                if it["note"] != "—":
                    note_badge = f'<span class="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded font-medium">{it["note"]}</span>'
                else:
                    note_badge = '<span class="text-gray-400">—</span>'
                    
                gender_badge = f'<span class="px-2 py-0.5 text-xs rounded font-medium {"bg-blue-100 text-blue-800" if it["gender"] == "Nam" else "bg-purple-100 text-purple-800"}">{it["gender"]}</span>'

                rows_html.append(f"""
                <tr class="{bg_class} border-b border-gray-200 hover:bg-blue-50 transition-colors">
                    <td class="py-2.5 px-3 text-center text-gray-600 font-mono text-xs">{idx}</td>
                    <td class="py-2.5 px-3 font-semibold text-gray-900">{it["model_name"]}</td>
                    <td class="py-2.5 px-3 text-center font-mono font-medium text-gray-700">{it["quota_city_str"]}</td>
                    <td class="py-2.5 px-3 text-center font-bold text-emerald-700 text-sm bg-emerald-50/50">{it["remaining_needed"]}</td>
                    <td class="py-2.5 px-3 text-center">{gender_badge}</td>
                    <td class="py-2.5 px-3 text-center font-mono text-gray-700">{it["first_time_str"]}</td>
                    <td class="py-2.5 px-3 text-center font-mono text-gray-700">{it["replacement_str"]}</td>
                    <td class="py-2.5 px-3 text-center font-mono text-gray-700">{it["additional_str"]}</td>
                    <td class="py-2.5 px-3">{note_badge}</td>
                </tr>
                """)
            return "\n".join(rows_html)

        html_template = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Báo Cáo Quota {city} - Dự án {project_code} ({quota_date})</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @media print {{
            .page-break {{ page-break-after: always; }}
            .no-print {{ display: none !important; }}
        }}
        body {{ font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif; }}
    </style>
</head>
<body class="bg-gray-100 p-4 md:p-8 text-gray-800">
    <div class="max-w-6xl mx-auto space-y-8">
        
        <!-- Nút In ấn / Xuất file nhanh -->
        <div class="no-print flex justify-end gap-3 mb-4">
            <button onclick="window.print()" class="bg-blue-700 hover:bg-blue-800 text-white font-medium px-4 py-2 rounded-lg shadow-sm flex items-center gap-2">
                In Báo Cáo / Lưu PDF
            </button>
        </div>

        <!-- TRANG 1: DỰ ĐỊNH MUA -->
        <div class="bg-white p-6 md:p-8 rounded-xl shadow-md border border-gray-200 page-break">
            <div class="border-b-2 border-slate-800 pb-4 mb-6">
                <div class="flex justify-between items-start gap-4">
                    <div>
                        <h1 class="text-2xl font-bold tracking-tight text-slate-900">BÁO CÁO QUOTA TP.{city} | DỰ ĐỊNH MUA</h1>
                        <p class="text-sm text-gray-500 mt-1">Dự án {project_code} | Ngày {quota_date} | {intenders.get("count_models", 0)} dòng xe còn quota | {intenders.get("total_remaining", 0)} đáp viên còn thiếu</p>
                    </div>
                    <div class="flex flex-col items-end gap-1 shrink-0">
                        <span class="font-bold text-xs tracking-wider text-slate-800 uppercase">VINAMR RESEARCH</span>
                        <span class="bg-emerald-100 text-emerald-800 text-xs font-semibold px-3 py-1 rounded-full uppercase tracking-wider">Nhóm Dự Định</span>
                    </div>
                </div>
            </div>

            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse text-sm">
                    <thead>
                        <tr class="bg-slate-800 text-white text-xs uppercase tracking-wider">
                            <th class="py-3 px-3 text-center">STT</th>
                            <th class="py-3 px-3">Mẫu xe</th>
                            <th class="py-3 px-3 text-center">Quota {city}<br><span class="text-[10px] text-slate-300 font-normal">(Đạt/Mục tiêu)</span></th>
                            <th class="py-3 px-3 text-center bg-slate-900 font-bold">Còn thiếu</th>
                            <th class="py-3 px-3 text-center">Giới tính</th>
                            <th class="py-3 px-3 text-center">Sở hữu<br>lần đầu¹</th>
                            <th class="py-3 px-3 text-center">Đổi xe /<br>Thay xe¹</th>
                            <th class="py-3 px-3 text-center">Mua<br>thêm xe¹</th>
                            <th class="py-3 px-3">Lưu ý</th>
                        </tr>
                    </thead>
                    <tbody>
                        {render_table_rows(intenders.get("items", []))}
                    </tbody>
                    <tfoot>
                        <tr class="bg-slate-900 text-white font-bold">
                            <td colspan="3" class="py-3 px-3 text-center uppercase tracking-wider">TỔNG</td>
                            <td class="py-3 px-3 text-center text-emerald-400 text-base">{intenders.get("total_remaining", 0)}</td>
                            <td colspan="5"></td>
                        </tr>
                    </tfoot>
                </table>
            </div>

            <div class="mt-6 text-xs text-gray-500 space-y-1">
                <p>¹ Ba cột hình thức thể hiện quota còn trống của nhóm Dự định tại cấp toàn mẫu sau khi đối chiếu quota hình thức tổng và phân khúc; không phải quota riêng TP.{city}.</p>
                <p>“Còn thiếu” là mức tuyển theo từng dòng xe sau khi kiểm tra TOTAL, Vùng miền, TP.{city}, Tình trạng sở hữu, Giới tính và Hình thức mua xe.</p>
            </div>

            <div class="mt-6 pt-4 border-t border-gray-200">
                <h3 class="text-xs font-bold text-red-700 uppercase tracking-wider mb-2">LƯU Ý QUOTA KHỐNG CHẾ</h3>
                <ul class="text-xs text-gray-700 space-y-1">
                    {''.join([f'<li>{gn}</li>' for gn in general_notes])}
                </ul>
            </div>
        </div>

        <!-- TRANG 2: ĐÃ SỞ HỮU -->
        <div class="bg-white p-6 md:p-8 rounded-xl shadow-md border border-gray-200">
            <div class="border-b-2 border-slate-800 pb-4 mb-6">
                <div class="flex justify-between items-start gap-4">
                    <div>
                        <h1 class="text-2xl font-bold tracking-tight text-slate-900">BÁO CÁO QUOTA TP.{city} | ĐÃ SỞ HỮU</h1>
                        <p class="text-sm text-gray-500 mt-1">Dự án {project_code} | Ngày {quota_date} | {owners.get("count_models", 0)} dòng xe còn quota | {owners.get("total_remaining", 0)} đáp viên còn thiếu</p>
                    </div>
                    <div class="flex flex-col items-end gap-1 shrink-0">
                        <span class="font-bold text-xs tracking-wider text-slate-800 uppercase">VINAMR RESEARCH</span>
                        <span class="bg-blue-100 text-blue-800 text-xs font-semibold px-3 py-1 rounded-full uppercase tracking-wider">Nhóm Đã Sở Hữu</span>
                    </div>
                </div>
            </div>

            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse text-sm">
                    <thead>
                        <tr class="bg-slate-800 text-white text-xs uppercase tracking-wider">
                            <th class="py-3 px-3 text-center">STT</th>
                            <th class="py-3 px-3">Mẫu xe</th>
                            <th class="py-3 px-3 text-center">Quota {city}<br><span class="text-[10px] text-slate-300 font-normal">(Đạt/Mục tiêu)</span></th>
                            <th class="py-3 px-3 text-center bg-slate-900 font-bold">Còn thiếu</th>
                            <th class="py-3 px-3 text-center">Giới tính</th>
                            <th class="py-3 px-3 text-center">Sở hữu<br>lần đầu¹</th>
                            <th class="py-3 px-3 text-center">Đổi xe /<br>Thay xe¹</th>
                            <th class="py-3 px-3 text-center">Mua<br>thêm xe¹</th>
                            <th class="py-3 px-3">Lưu ý</th>
                        </tr>
                    </thead>
                    <tbody>
                        {render_table_rows(owners.get("items", []))}
                    </tbody>
                    <tfoot>
                        <tr class="bg-slate-900 text-white font-bold">
                            <td colspan="3" class="py-3 px-3 text-center uppercase tracking-wider">TỔNG</td>
                            <td class="py-3 px-3 text-center text-emerald-400 text-base">{owners.get("total_remaining", 0)}</td>
                            <td colspan="5"></td>
                        </tr>
                    </tfoot>
                </table>
            </div>

            <div class="mt-6 text-xs text-gray-500 space-y-1">
                <p>¹ Ba cột hình thức thể hiện quota còn trống của nhóm Đã sở hữu tại cấp toàn mẫu sau khi đối chiếu quota hình thức tổng và phân khúc; không phải quota riêng TP.{city}.</p>
                <p>“Còn thiếu” là mức tuyển theo từng dòng xe sau khi kiểm tra TOTAL, Vùng miền, TP.{city}, Tình trạng sở hữu, Giới tính và Hình thức mua xe.</p>
            </div>
        </div>

    </div>
</body>
</html>"""
        return html_template
