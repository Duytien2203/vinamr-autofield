"""
VINAMR Field - Hệ Thống Quản Lý & Trực Quan Hóa Quota Tuyển Dụng Ô Tô
Ứng dụng Web chuyên dụng cho Điều phối & Nhân viên tuyển dụng hiện trường (Recruiters).
"""

import os
import sys
import mimetypes

# Khắc phục quyền đọc Registry trên Windows sandbox
if hasattr(mimetypes, "_mimetypes_read_windows_registry"):
    mimetypes._mimetypes_read_windows_registry = lambda add_type: None

import streamlit as st
from datetime import datetime
import pandas as pd

# Đường dẫn gốc
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from core.parser import QuotaParser, extract_metadata_from_filename
from core.engine import QuotaEngine
from core.reporter import QuotaReporter
from database.db import init_db, save_upload, get_available_dates, get_upload_data, get_all_uploads_summary

# 1. Cấu hình Trang Streamlit
st.set_page_config(
    page_title="VINAMR Field - Quản Lý Quota Ô Tô",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Khởi tạo Database và nạp dữ liệu mẫu nếu chưa có
init_db()

def bootstrap_sample_data():
    dates = get_available_dates("0747")
    if not dates:
        sample_path = os.path.join(BASE_DIR, "data", "samples", "sample_quota_0747_20261106.xml")
        if os.path.exists(sample_path):
            parsed = QuotaParser.parse_xml_spreadsheet(sample_path)
            save_upload("0747", "2026-11-06", "file quota 06/11", sample_path, parsed)

bootstrap_sample_data()

# 3. Custom CSS chuyên nghiệp, hiện đại, tối ưu trải nghiệm người dùng
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header card */
    .header-card {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Metrics box */
    .metric-container {
        display: flex;
        gap: 16px;
        margin-bottom: 20px;
    }
    .metric-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px 20px;
        flex: 1;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        border-left: 4px solid #2563EB;
    }
    .metric-card.accent {
        border-left-color: #059669;
    }
    .metric-card.warning {
        border-left-color: #D97706;
    }
    .metric-title {
        font-size: 0.82rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0F172A;
        margin-top: 4px;
    }
    .metric-desc {
        font-size: 0.78rem;
        color: #94A3B8;
        margin-top: 2px;
    }
    
    /* Table styling */
    .dataframe {
        width: 100% !important;
        border-collapse: collapse !important;
        font-size: 0.88rem !important;
    }
    .dataframe th {
        background-color: #1E293B !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 10px 12px !important;
        text-align: center !important;
    }
    .dataframe td {
        padding: 8px 12px !important;
        border-bottom: 1px solid #E2E8F0 !important;
    }
    
    /* Custom Badges */
    .badge-male {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 2px 8px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .badge-both {
        background-color: #F3E8FF;
        color: #6B21A8;
        padding: 2px 8px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .badge-note {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 500;
        font-size: 0.75rem;
    }
    
    /* Khung lưu ý */
    .notice-box {
        background-color: #FFFBEB;
        border: 1px solid #FDE68A;
        border-radius: 8px;
        padding: 14px 18px;
        margin-top: 18px;
        font-size: 0.83rem;
        color: #78350F;
    }
</style>
""", unsafe_allow_html=True)

# 4. THANH BÊN (SIDEBAR) - ĐIỀU KHIỂN & TẢI FILE
with st.sidebar:
    st.markdown("### **VINAMR OPERATIONS**")
    st.caption("Hệ Thống Giám Sát & Quota Tuyển Dụng")
    
    st.divider()
    
    # Chọn Bảng hỏi / Dự án
    project_code = st.selectbox(
        "Chọn Dự án / Bảng hỏi:",
        ["0747", "0748"],
        format_func=lambda x: f"Dự án {x}"
    )
    
    # Lấy danh sách ngày có dữ liệu cho dự án đã chọn
    available_dates = get_available_dates(project_code)
    
    if available_dates:
        selected_date = st.selectbox(
            "Chọn Ngày Quota:",
            available_dates,
            index=0
        )
    else:
        st.warning(f"Chưa có file quota cho dự án {project_code}. Vui lòng tải file lên bên dưới.")
        selected_date = None

    # Bộ lọc Tỉnh / Thành phố
    target_city = st.selectbox(
        "Khu vực / Thành phố:",
        ["HCM", "Hà Nội", "Đà Nẵng", "Hải Phòng", "Nghệ An", "Cần Thơ"],
        index=0
    )

    st.divider()

    # Khu vực dành cho Sếp tải file Quota
    with st.expander("**Dành cho Quản Lý: Tải file Quota mới**", expanded=False):
        st.markdown("**Cập nhật dữ liệu hàng ngày (Tự động nhận diện):**")
        
        uploaded_file = st.file_uploader(
            "Kéo thả hoặc chọn file Quota:", 
            type=["xml", "xlsx", "xls"],
            key="file_uploader"
        )
        
        if uploaded_file is not None:
            # Tự động nhận diện Dự án và Ngày áp dụng từ tên file
            auto_project, auto_date_str = extract_metadata_from_filename(uploaded_file.name)
            
            st.success(f"""
            **Hệ thống đã nhận diện tự động:**
            * Dự án phân loại: **Dự án {auto_project}**
            * Ngày áp dụng: **{auto_date_str}**
            """)
            
            if st.button("Xác nhận & Cập nhật Quota", type="primary"):
                try:
                    file_bytes = uploaded_file.read()
                    
                    # Lưu file vật lý
                    save_dir = os.path.join(BASE_DIR, "data", "uploads", auto_project)
                    os.makedirs(save_dir, exist_ok=True)
                    saved_path = os.path.join(save_dir, f"{auto_date_str}_{uploaded_file.name}")
                    with open(saved_path, "wb") as f:
                        f.write(file_bytes)
                    
                    # Phân tích file XML SpreadsheetML
                    parsed = QuotaParser.parse_xml_spreadsheet(saved_path)
                    
                    # Lưu vào Database
                    save_upload(auto_project, auto_date_str, uploaded_file.name, saved_path, parsed)
                    st.success(f"Đã cập nhật thành công Dự án {auto_project} ngày {auto_date_str}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi phân tích file: {str(e)}")

# 5. GIAO DIỆN CHÍNH (MAIN DASHBOARD)
if not selected_date:
    st.info("Vui lòng tải file quota từ thanh bên trái để bắt đầu xem báo cáo tuyển dụng.")
    st.stop()

# Đọc dữ liệu đã phân tích từ database
data_record = get_upload_data(project_code, selected_date)
if not data_record:
    st.error("Không tìm thấy dữ liệu cho ngày đã chọn!")
    st.stop()

parsed_data = data_record["parsed_data"]

# Chạy Quota Engine tính toán cho Thành phố đã chọn
analysis_result = QuotaEngine.analyze(parsed_data, target_city=target_city)

intenders_data = analysis_result["intenders"]
owners_data = analysis_result["owners"]
general_notes = analysis_result["general_notes"]

# Header banner
st.markdown(f"""
<div class="header-card">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h2 style="margin: 0; font-size: 1.6rem; font-weight: 700;">DỰ ÁN {project_code} | QUOTA TP.{target_city.upper()}</h2>
            <p style="margin: 4px 0 0 0; color: #94A3B8; font-size: 0.9rem;">
                Cập nhật ngày: <b style="color: white;">{selected_date}</b> • Nguồn: <i>{data_record['file_name']}</i>
            </p>
        </div>
        <div style="text-align: right;">
            <span style="background: rgba(37, 99, 235, 0.2); border: 1px solid #3B82F6; color: #60A5FA; padding: 6px 14px; border-radius: 20px; font-weight: 600; font-size: 0.85rem;">
                Khu vực {analysis_result['region']}
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# KPI Cards
total_intender_missing = intenders_data["total_remaining"]
intender_models_count = intenders_data["count_models"]
total_owner_missing = owners_data["total_remaining"]
owner_models_count = owners_data["count_models"]
total_missing_all = total_intender_missing + total_owner_missing

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="metric-card accent">
        <div class="metric-title">Tổng Còn Thiếu TP.{target_city}</div>
        <div class="metric-value">{total_missing_all}</div>
        <div class="metric-desc">Tất cả các dòng xe cần tuyển</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Nhóm Dự Định Mua</div>
        <div class="metric-value">{total_intender_missing}</div>
        <div class="metric-desc">{intender_models_count} dòng xe còn chỉ tiêu</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Nhóm Đã Sở Hữu</div>
        <div class="metric-value">{total_owner_missing}</div>
        <div class="metric-desc">{owner_models_count} dòng xe còn chỉ tiêu</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    # Nút tải báo cáo nhanh
    st.markdown('<div class="metric-card warning"><div class="metric-title">Xuất Báo Cáo Tuyển Dụng</div>', unsafe_allow_html=True)
    excel_bytes = QuotaReporter.generate_excel(analysis_result, project_code, selected_date)
    html_report = QuotaReporter.generate_html(analysis_result, project_code, selected_date)
    
    st.download_button(
        label="📥 Tải Excel Báo Cáo",
        data=excel_bytes,
        file_name=f"Bao_Cao_Quota_{project_code}_{target_city}_{selected_date}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.write("")

# 6. CÁC TABS HIỂN THỊ DỮ LIỆU
tab_intender, tab_owner, tab_checker, tab_notes = st.tabs([
    f"Dự Định Mua ({intender_models_count} dòng xe | {total_intender_missing} chỉ tiêu)",
    f"Đã Sở Hữu ({owner_models_count} dòng xe | {total_owner_missing} chỉ tiêu)",
    "Kiểm Tra Đáp Viên Nhanh (Checker)",
    "Lưu Ý Quota Khống Chế & Quy Tắc"
])

def render_interactive_table(items: list, target_city: str, is_intender: bool):
    if not items:
        st.success(f"🎉 Nhóm này tại TP.{target_city} đã hoàn thành 100% quota! Không cần tuyển thêm.")
        return

    # Ô tìm kiếm xe
    search_q = st.text_input("🔍 Tìm kiếm nhanh mẫu xe:", "", key=f"search_{'int' if is_intender else 'own'}")
    
    filtered_items = [
        it for it in items 
        if search_q.lower() in it["model_name"].lower() or search_q.lower() in it["segment"].lower()
    ]
    
    table_data = []
    for idx, it in enumerate(filtered_items, start=1):
        table_data.append({
            "STT": idx,
            "Phân khúc": it["segment"],
            "Mẫu xe": it["model_name"],
            f"Quota {target_city}": it["quota_city_str"],
            "Còn thiếu": it["remaining_needed"],
            "Giới tính tuyển": it["gender"],
            "Sở hữu lần đầu¹": it["first_time_str"],
            "Đổi xe / Thay xe¹": it["replacement_str"],
            "Mua thêm xe¹": it["additional_str"],
            "Lưu ý khống chế": it["note"]
        })
        
    df = pd.DataFrame(table_data)
    
    # Hiển thị bảng định dạng đẹp mắt
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "STT": st.column_config.NumberColumn(width="small"),
            "Còn thiếu": st.column_config.NumberColumn(
                help="Số lượng đáp viên thực tế cần tìm sau khi trừ các giới hạn trần",
                width="small"
            ),
            "Giới tính tuyển": st.column_config.TextColumn(width="medium"),
            "Lưu ý khống chế": st.column_config.TextColumn(width="large"),
        }
    )
    
    st.caption("¹ Ba cột hình thức thể hiện quota còn trống tại cấp toàn mẫu sau khi đối chiếu quota hình thức tổng và phân khúc; không phải quota riêng thành phố.")

with tab_intender:
    st.subheader(f"Danh sách xe Dự Định Mua còn Quota tại TP.{target_city}")
    render_interactive_table(intenders_data["items"], target_city, is_intender=True)

with tab_owner:
    st.subheader(f"Danh sách xe Đã Sở Hữu còn Quota tại TP.{target_city}")
    render_interactive_table(owners_data["items"], target_city, is_intender=False)

with tab_checker:
    st.subheader("Công cụ Kiểm Tra Đáp Viên Hiện Trường (Instant Candidate Validator)")
    st.write("Khi tìm thấy 1 đáp viên, nhân viên điền thông tin bên dưới để kiểm tra ngay xem có được nhận hay không:")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        # Danh sách tất cả xe trong hệ thống
        all_models = sorted(list(set(
            [x["model_name"] for x in intenders_data["items"]] + 
            [x["model_name"] for x in owners_data["items"]]
        )))
        chk_model = st.selectbox("Chọn mẫu xe của đáp viên:", all_models)
        
    with c2:
        chk_status = st.selectbox("Tình trạng sở hữu:", ["Dự định mua", "Đã sở hữu"])
        
    with c3:
        chk_gender = st.selectbox("Giới tính đáp viên:", ["Nam", "Nữ"])
        
    with c4:
        chk_ptype = st.selectbox("Hình thức mua xe:", ["Sở hữu lần đầu", "Đổi xe / Thay xe", "Mua thêm xe"])
        
    # Logic kiểm tra đáp viên
    active_pool = intenders_data["items"] if chk_status == "Dự định mua" else owners_data["items"]
    matched = next((x for x in active_pool if x["model_name"] == chk_model), None)
    
    if st.button("🔎 Kiểm tra tính hợp lệ", type="primary"):
        if not matched:
            st.error(f"❌ **KHÔNG NHẬN ĐÁP VIÊN NÀY:** Mẫu xe **{chk_model}** ở nhóm **{chk_status}** đã hết quota tại TP.{target_city} hoặc đã bị khóa!")
        else:
            # Kiểm tra giới tính
            allowed_gender = matched["gender"]
            gender_ok = (allowed_gender == "Nam / Nữ") or (chk_gender in allowed_gender)
            
            # Kiểm tra hình thức mua
            pt_col = "first_time_str" if chk_ptype == "Sở hữu lần đầu" else ("replacement_str" if chk_ptype == "Đổi xe / Thay xe" else "additional_str")
            pt_val = matched[pt_col]
            pt_ok = pt_val != "—" and int(pt_val) > 0 if pt_val.isdigit() else False
            
            if not gender_ok:
                st.error(f"❌ **TỪ CHỐI GIỚI TÍNH:** Mẫu xe {chk_model} hiện chỉ tuyển **{allowed_gender}** (đáp viên là {chk_gender} đã vượt/đạt chỉ tiêu!).")
            elif not pt_ok:
                st.error(f"❌ **TỪ CHỐI HÌNH THỨC MUA:** Hình thức **{chk_ptype}** của xe {chk_model} đã đủ quota (giá trị hiện tại: —). Hãy tìm đáp viên có hình thức khác còn trống!")
            else:
                st.success(f"""
                ✅ **ĐÁP VIÊN HỢP LỆ - CÓ THỂ NHẬN PHỎNG VẤN!**
                * **Mẫu xe:** {chk_model} ({chk_status})
                * **Khu vực:** TP.{target_city} (Còn thiếu thực tế: **{matched['remaining_needed']}** đáp viên)
                * **Giới tính hợp lệ:** {chk_gender} (Quy định: {allowed_gender})
                * **Hình thức hợp lệ:** {chk_ptype} (Quota hình thức còn: {pt_val})
                """)

with tab_notes:
    st.subheader("Lưu Ý Quota Khống Chế & Nguyên Tắc Tính Toán")
    for gn in general_notes:
        st.markdown(f"- {gn}")
        
    st.markdown("""
    ---
    ### 📌 Giải thích các quy tắc ràng buộc đa tầng:
    1. **Khống chế theo Phân khúc:** Nếu tổng chỉ tiêu của một phân khúc (VD: D-SUV Dự định) đã đạt 100%, tất cả các dòng xe con trong phân khúc đó đều dừng tuyển dù ở cấp thành phố vẫn còn chỉ tiêu.
    2. **Khống chế Vùng miền:** Số lượng tuyển thực tế tại một thành phố không được vượt quá số lượng còn lại của toàn vùng miền đó (VD: TP.HCM thiếu 8 nhưng miền Nam chỉ thiếu 7 thì lấy trần 7).
    3. **Khống chế Hình thức mua xe:** Nếu tổng quota của các hình thức được phép (Lần đầu + Đổi + Mua thêm) nhỏ hơn số thiếu của thành phố, số tuyển thực tế sẽ bị giới hạn bằng tổng hình thức.
    4. **Khống chế Giới tính:** Tự động khóa giới tính Nữ hoặc Nam khi giới tính đó đã đạt hoặc vượt chỉ tiêu ở cấp toàn mẫu hoặc cấp phân khúc.
    """)
