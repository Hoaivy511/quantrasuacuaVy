import os
import re
import urllib.parse
import unicodedata
from datetime import datetime
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# CẤU HÌNH & HẰNG SỐ CƠ BẢN
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else "."
HISTORY_FILE = os.path.join(BASE_DIR, "sales_history.csv")

# Cấu hình ảnh & nút co giãn full chiều rộng
FULL_IMG = {"use_container_width": True}
FULL_BTN = {"use_container_width": True}
FULL_DF = {"use_container_width": True}

# Thông tin tài khoản nhận tiền
BANK_ID = "agribank"
ACCOUNT_NO = "1234567890"
ACCOUNT_NAME = "NGUYEN THI HOANG VY"

# ---------------------------------------------------------
# DỮ LIỆU MENU TRÀ SỮA & OPTIONS
# ---------------------------------------------------------
MENU_TEA = {
    "Trà Sữa Truyền Thống 🧋": {
        "price": 25000,
        "category": "Trà Sữa",
        "image": "https://unsplash.com"
    },
    "Trà Sữa Matcha Khoai Môn 🍵": {
        "price": 30000,
        "category": "Trà Sữa",
        "image": "https://unsplash.com"
    },
    "Trà Thạch Đào 🍑": {
        "price": 28000,
        "category": "Trà Trái Cây",
        "image": "https://unsplash.com"
    },
    "Trà Dâu Tây Nhiệt Đới 🍓": {
        "price": 28000,
        "category": "Trà Trái Cây",
        "image": "https://unsplash.com"
    }
}

SIZE_OPTIONS = {"Size M (Vừa)": 0, "Size L (Lớn) (+5k)": 5000}
SUGAR_LEVELS = ["100% Đường", "70% Đường", "50% Đường", "0% Không Đường"]
ICE_LEVELS = ["100% Đá", "70% Đá", "50% Đá", "0% Không Đá"]
TOPPING_OPTIONS = {
    "Trân châu đen 🧋": 5000,
    "Trân châu trắng 💎": 5000,
    "Thạch phô mai 🧀": 7000,
    "Pudding trứng 🍮": 7000
}

HISTORY_COLS = ["time", "customer", "total_items", "final_amount"]

# ---------------------------------------------------------
# CÁC HÀM XỬ LÝ LOGIC (BỔ SUNG & HOÀN THIỆN)
# ---------------------------------------------------------
if "cart" not in st.session_state:
    st.session_state.cart = []
if "invoice" not in st.session_state:
    st.session_state.invoice = None

def load_history() -> list:
    try:
        if os.path.exists(HISTORY_FILE):
            return pd.read_csv(HISTORY_FILE).to_dict("records")
    except Exception:
        pass
    return []

def save_history(rows: list) -> None:
    try:
        pd.DataFrame(rows, columns=HISTORY_COLS).to_csv(HISTORY_FILE, index=False)
    except Exception:
        pass

def to_ascii(text: str, max_len: int = 25) -> str:
    if not text:
        return "Khach"
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^A-Za-z0-9 ]", "", text).strip()
    return text[:max_len] or "Khach"

def clean_topping(label: str) -> str:
    return label.rsplit(" ", 1)[0] if " " in label else label

def create_txt_invoice(inv: dict) -> str:
    line = "=" * 40
    content = f"{line}\n{'HÓA ĐƠN BÁN HÀNG - quantrasuacuaVy':^40}\n{line}\n"
    content += f"Thời gian: {inv['time']}\n"
    content += f"Khách hàng: {inv['customer']}\n"
    if inv["note"]:
        content += f"Ghi chú: {inv['note']}\n"
    content += f"{'-' * 40}\n"
    for idx, item in enumerate(inv["cart"], 1):
        content += f"{idx}. {item['Tên món']} ({item['Size']})\n"
        content += f"   - Đường: {item['Đường']} | Đá: {item['Đá']}\n"
        if item["Topping"] != "Không":
            content += f"   - Topping: {item['Topping']}\n"
        content += f"   SL: {item['Số lượng']} x {item['Đơn giá']:,} = {item['Thành tiền']:,} VNĐ\n"
    content += f"{'-' * 40}\n"
    content += f"Tổng tiền món: {inv['total']:,} VNĐ\n"
    content += f"Giảm giá: {inv['discount']}%\n"
    content += f"TỔNG THANH TOÁN: {inv['final']:,} VNĐ\n"
    content += f"{line}\n{'Cảm ơn bạn đã ủng hộ quantrasuacuaVy! 💕':^40}\n"
    return content

def show_payment_qr(inv: dict) -> None:
    raw_name = inv["customer"] if inv["customer"].strip() else "Khach"
    add_info_text = f"TT {to_ascii(raw_name)}"
    qr_url = (
        f"https://img.vietqr.io/image/{BANK_ID}-{ACCOUNT_NO}-compact2.png"
        f"?amount={inv['final']}"
        f"&addInfo={urllib.parse.quote(add_info_text)}"
        f"&accountName={urllib.parse.quote(ACCOUNT_NAME)}"
    )
    st.success("🎉 Đã tạo đơn! Quét mã QR để chuyển khoản:")
    st.image(qr_url, caption="Mã QR Agribank Tự Động", **trasua.jpg)
    st.link_button("🔗 Mở mã QR ở tab mới (nếu ảnh không hiện)", qr_url)
    
    st.markdown("### 📲 Thông Tin Chuyển Khoản")
    st.write("🏦 **Ngân hàng:** Agribank")
    st.write(f"💳 **Số tài khoản:** `{ACCOUNT_NO}`")
    st.write(f"👤 **Chủ tài khoản:** {ACCOUNT_NAME}")
    st.write(f"💰 **Số tiền thanh toán:** `{inv['final']:,} VNĐ`")
    st.write(f"📝 **Nội dung chuyển khoản:** `{add_info_text}`")
    st.caption("⬇️ Kéo xuống dưới để xem hóa đơn chi tiết và tải file.")

# ---------------------------------------------------------
# GIAO DIỆN CHÍNH (TIÊU ĐỀ & TABS)
# ---------------------------------------------------------
st.set_page_config(page_title="quantrasuacuaVy", layout="wide", page_icon="🧋")

st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>🧋 quantrasuacuaVy 🌪️</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic;'>✨ Đậm vị trà - Đậm gu Gen Z ✨</p>", unsafe_allow_html=True)

tab_order, tab_dashboard = st.tabs(["🛍️ Đặt Món & Thanh Toán", "📊 Báo Cáo Doanh Thu"])

# =========================================================
# TAB 1: ĐẶT MÓN & THANH TOÁN
# =========================================================
with tab_order:
    col_left, col_right = st.columns([1.25, 0.75])

    # ---------------- CỘT TRÁI: MENU ODER ----------------
    with col_left:
        st.subheader("📋 Chọn Món Đồ Uống")

        c_search, c_filter = st.columns([2, 1])
        with c_search:
            search_query = st.text_input("🔍 Tìm tên món:", placeholder="Ví dụ: Matcha, Thái xanh...")
        with c_filter:
            category_filter = st.selectbox("📂 Danh mục:", ["Tất cả", "Trà Sữa", "Trà Trái Cây"])

        filtered_menu = {
            k: v
            for k, v in MENU_TEA.items()
            if (category_filter == "Tất cả" or v["category"] == category_filter)
            and (search_query.strip().lower() in k.lower())
        }

        if not filtered_menu:
            st.warning("Không tìm thấy món phù hợp!")
        else:
            selected_tea = st.selectbox("🥤 Chọn món uống:", list(filtered_menu.keys()))
            tea_info = MENU_TEA[selected_tea]

            with st.container(border=True):
                col_pic, col_opt = st.columns([1, 1.1])
                with col_pic:
                    st.image(tea_info["image"], caption=selected_tea, **FULL_IMG)
                with col_opt:
                    quantity = st.number_input("🔢 Số lượng:", min_value=1, value=1, step=1)
                    selected_size = st.selectbox("📏 Size:", list(SIZE_OPTIONS.keys()))
                    selected_sugar = st.selectbox("🍬 Đường:", SUGAR_LEVELS)
                    selected_ice = st.selectbox("🧊 Đá:", ICE_LEVELS)

                selected_toppings = st.multiselect("✨ Topping thêm:", options=list(TOPPING_OPTIONS.keys()))

                unit_price = (
                    tea_info["price"]
                    + SIZE_OPTIONS[selected_size]
                    + sum(TOPPING_OPTIONS[t] for t in selected_toppings)
                )
                item_total = unit_price * int(quantity)

                st.info(f"💡 Đơn giá: {unit_price:,} VNĐ / ly | Tổng cộng: {item_total:,} VNĐ")

                if st.button("➕ THÊM VÀO GIỎ HÀNG", type="primary", **FULL_BTN):
                    topping_str = (
                        ", ".join(clean_topping(t) for t in selected_toppings)
                        if selected_toppings
                        else "Không"
                    )
                    st.session_state.cart.append(
                        {
                            "Tên món": selected_tea,
                            "Size": selected_size.split()[0],
                            "Đường": selected_sugar.split()[0],
                            "Đá": selected_ice.split()[0],
                            "Topping": topping_str,
                            "Đơn giá": unit_price,
                            "Số lượng": int(quantity),
                            "Thành tiền": item_total,
                        }
                    )
                    st.session_state.invoice = None   
                    st.toast(f"Đã thêm {quantity}x {selected_tea} vào giỏ!", icon="🧋")

    # ---------------- CỘT PHẢI: GIỎ HÀNG & THANH TOÁN ----------------
    with col_right:
        st.subheader("🛒 Giỏ Hàng Mua Sắm")

        customer_name = st.text_input("👤 Tên khách hàng:", placeholder="Tên khách hàng...")
        order_note = st.text_input("📝 Ghi chú đơn hàng:", placeholder="Ví dụ: Mang đi, Ít ngọt...")

        if not st.session_state.cart:
            st.info("Giỏ hàng đang trống!")
        else:
            df_cart = pd.DataFrame(st.session_state.cart)
            st.dataframe(
                df_cart[["Tên món", "Size", "Topping", "Số lượng", "Thành tiền"]],
                hide_index=True,
                **FULL_DF,
            )

            # --- Logic Xóa Món ---
            rm_options = [
                f"{i + 1}. {r['Tên món']} ({r['Size']}) x{r['Số lượng']}"
                for i, r in enumerate(st.session_state.cart)
            ]
            rm_choice = st.selectbox("❌ Xóa 1 món khỏi giỏ:", ["— Chọn món —"] + rm_options)
            
            if rm_choice != "— Chọn món —":
                idx_to_remove = int(rm_choice.split(".")[0]) - 1
                if st.button("🗑️ Xác nhận xóa món này", **FULL_BTN):
                    st.session_state.cart.pop(idx_to_remove)
                    st.session_state.invoice = None
                    st.rerun()
           # Kiểm tra nếu giỏ hàng có sản phẩm mới hiện nút mua
        if not st.session_state.cart:
            st.info("Giỏ hàng đang trống!")
        else:
            df_cart = pd.DataFrame(st.session_state.cart)
            st.dataframe(df_cart[["Tên món", "Size", "Topping", "Số lượng", "Thành tiền"]], hide_index=True, **FULL_DF)
            
            # (Các đoạn tính tiền, giảm giá...)
            # Nút chốt đơn và xuất hóa đơn
            if st.button("🚀 XUẤT HÓA ĐƠN & THANH TOÁN", type="primary", **FULL_BTN):
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cust_title = customer_name.strip() if customer_name.strip() else "Khách vãng lai"
                
                # Tạo đối tượng Invoice lưu vào Session State
                st.session_state.invoice = {
                    "time": now_str,
                    "customer": cust_title,
                    "note": order_note,
                    "cart": st.session_state.cart.copy(),
                    "total": total_bill,
                    "discount": discount_pct,
                    "final": final_bill
                }

                # Lưu vào lịch sử bán hàng (CSV)
                history = load_history()
                history.append({
                    "time": now_str,
                    "customer": cust_title,
                    "total_items": sum(item["Số lượng"] for item in st.session_state.cart),
                    "final_amount": final_bill
                })
                save_history(history)
                
                # Xóa giỏ hàng sau khi xuất đơn thành công
                st.session_state.cart = []
                
                # 🎈 THÊM HIỆU ỨNG BONG BÓNG BAY LÊN Ở ĐÂY:
                st.balloons()
                
                # Ép tải lại trang để hiển thị hóa đơn và mã QR
                st.rerun()
