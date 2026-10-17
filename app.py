import streamlit as st

if "cart" not in st.session_state:
    st.session_state.cart = []
if "invoice" not in st.session_state:
    st.session_state.invoice = None      # ảnh chụp đơn đã tạo (chống lệch số tiền)
HISTORY_COLS = ["time", "customer", "total_items", "final_amount"]


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
        pass  # môi trường chỉ-đọc: vẫn chạy bình thường, chỉ không lưu file


def to_ascii(text: str, max_len: int = 25) -> str:
    """Nội dung chuyển khoản ngân hàng không dấu, chỉ chữ/số/khoảng trắng."""
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^A-Za-z0-9 ]", "", text).strip()
    return text[:max_len] or "Khach"




def clean_topping(label: str) -> str:
    """Bỏ emoji ở cuối, giữ nguyên tên đầy đủ: 'Trân châu đen 🧋' -> 'Trân châu đen'."""
    return label.rsplit(" ", 1)[0]


def create_txt_invoice(inv: dict) -> str:
    line = "=" * 40
    content = f"{line}\n{'HÓA ĐƠN BÁN HÀNG - MR KHẢI LỐC XOÁY':^40}\n{line}\n"
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
    content += f"{line}\n{'Cảm ơn bạn đã ủng hộ Mr Khải Lốc Xoáy! 💕':^40}\n"
    return content


def show_payment_qr(inv: dict) -> None:
    """Hiện mã QR + thông tin chuyển khoản ngay dưới nút tạo đơn."""
    raw_name = inv["customer"] if inv["customer"] != "Khách vãng lai" else "Khach"
    add_info_text = f"TT {to_ascii(raw_name)}"
    qr_url = (
        f"https://img.vietqr.io/image/{BANK_ID}-{ACCOUNT_NO}-compact2.png"
        f"?amount={inv['final']}"
        f"&addInfo={urllib.parse.quote(add_info_text)}"
        f"&accountName={urllib.parse.quote(ACCOUNT_NAME)}"
    )
    st.success("🎉 Đã tạo đơn! Quét mã QR để chuyển khoản:")
    st.image(qr_url, caption="Mã QR Agribank Tự Động", **FULL_IMG)
    st.link_button("🔗 Mở mã QR ở tab mới (nếu ảnh không hiện)", qr_url)
    st.markdown("### 📲 Thông Tin Chuyển Khoản")
    st.write("🏦 **Ngân hàng:** Agribank")
    st.write(f"💳 **Số tài khoản:** `{ACCOUNT_NO}`")
    st.write(f"👤 **Chủ tài khoản:** {ACCOUNT_NAME}")
    st.write(f"💰 **Số tiền thanh toán:** `{inv['final']:,} VNĐ`")
    st.write(f"📝 **Nội dung chuyển khoản:** `{add_info_text}`")
    st.caption("⬇️ Kéo xuống dưới để xem hóa đơn chi tiết và tải file.")


# ---------------------------------------------------------
# TIÊU ĐỀ & TABS
# ---------------------------------------------------------
st.markdown("<h1 class='main-title'>🧋 TRÀ SỮA MR KHẢI LỐC XOÁY 🌪️</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>✨ Đậm vị trà - Đậm gu Gen Z ✨</p>", unsafe_allow_html=True)

BANNER = os.path.join(BASE_DIR, "trasua.jpg")
if os.path.exists(BANNER):
    _, c_mid, _ = st.columns([1, 2, 1])
    with c_mid:
        st.image(BANNER, **FULL_IMG)

tab_order, tab_dashboard = st.tabs(["🛍️ Đặt Món & Thanh Toán", "📊 Báo Cáo Doanh Thu"])

# =========================================================
# TAB 1: ĐẶT MÓN & THANH TOÁN
# =========================================================
with tab_order:
    col_left, col_right = st.columns([1.25, 0.75])

    # ---------------- CỘT TRÁI: MENU ----------------
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

                st.markdown(
                    f"<div class='price-badge'>💡 Đơn giá: {unit_price:,} VNĐ / ly</div>",
                    unsafe_allow_html=True,
                )
                st.write("")

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
                    st.session_state.invoice = None   # giỏ đổi -> hóa đơn cũ hết hiệu lực
                    st.toast(f"Đã thêm {quantity}x {selected_tea} vào giỏ!", icon="🧋")

    # ---------------- CỘT PHẢI: GIỎ HÀNG ----------------
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

            rm_options = [
                f"{i + 1}. {r['Tên món']} ({r['Size']}) x{r['Số lượng']}"
                for i, r in enumerate(st.session_state.cart)
            ]
            rm_choice = st.selectbox("❌ Xóa 1 món khỏi giỏ:", ["— Chọn món —"] + rm_options)
            if rm_choice != "— Chọn món —" and st.button("Xóa món đã chọn"):
                st.session_state.cart.pop(rm_options.index(rm_choice))
                st.session_state.invoice = None
                st.rerun()

            if st.button("🗑️ Xóa toàn bộ giỏ hàng"):
                st.session_state.cart = []
                st.session_state.invoice = None
                st.rerun()

            st.markdown("---")
            total_price = int(df_cart["Thành tiền"].sum())
            discount = st.number_input("🎁 Khuyến mãi (%):", min_value=0, max_value=100, value=0, step=5)
            final_price = int(total_price * (1 - discount / 100))

            st.markdown(f"### Tổng tạm tính: **{total_price:,} VNĐ**")
            if discount > 0:
                st.markdown(
                    f"### 🔥 Sau giảm giá: <span style='color:#FF477E'>{final_price:,} VNĐ</span>",
                    unsafe_allow_html=True,
                )

            if st.button("💳 TẠO ĐƠN & QUÉT MÃ QR", type="primary", **FULL_BTN):
                now = datetime.now(VN_TZ)
                customer = customer_name.strip() if customer_name.strip() else "Khách vãng lai"
                st.session_state.invoice = {
                    "time": now.strftime("%d/%m/%Y %H:%M:%S"),
                    "stamp": now.strftime("%Y%m%d_%H%M%S"),
                    "customer": customer,
                    "note": order_note.strip(),
                    "cart": [dict(i) for i in st.session_state.cart],
                    "total": total_price,
                    "discount": int(discount),
                    "final": final_price,
                }
                # đọc lại file chung rồi mới thêm, để đơn của nhiều người không ghi đè nhau
                shared_history = load_history()
                shared_history.append(
                    {
                        "time": st.session_state.invoice["time"],
                        "customer": customer,
                        "total_items": int(df_cart["Số lượng"].sum()),
                        "final_amount": final_price,
                    }
                )
                save_history(shared_history)
                st.balloons()

        if st.session_state.invoice:
            show_payment_qr(st.session_state.invoice)

    # ---------------- HIỂN THỊ MÃ QR & HÓA ĐƠN ----------------
    inv = st.session_state.invoice
    if inv:
        st.markdown("---")
        with st.container(border=True):
            st.markdown(
                "<h2 style='text-align: center; color: #FF477E;'>🧋 HÓA ĐƠN BÁN HÀNG - MR KHẢI LỐC XOÁY</h2>",
                unsafe_allow_html=True,
            )
            st.write(f"⏰ **Thời gian:** {inv['time']}")
            st.write(f"👤 **Khách hàng:** {inv['customer']}")
            if inv["note"]:
                st.write(f"📌 **Ghi chú:** {inv['note']}")

            st.table(
                pd.DataFrame(inv["cart"])[
                    ["Tên món", "Size", "Đường", "Đá", "Topping", "Số lượng", "Thành tiền"]
                ]
            )

            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**Tổng tiền:** {inv['total']:,} VNĐ")
                st.write(f"**Giảm giá:** {inv['discount']}%")
            with c2:
                st.markdown(
                    f"### TỔNG CỦA BẠN: <span style='color:#FF477E'>{inv['final']:,} VNĐ</span>",
                    unsafe_allow_html=True,
                )

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="📥 Tải hóa đơn file (.TXT)",
                data=create_txt_invoice(inv),
                file_name=f"HoaDon_{inv['stamp']}.txt",
                mime="text/plain",
                **FULL_TABLE_DL,
            )
        with col_dl2:
            if st.button("🔄 Đặt đơn tiếp theo", **FULL_BTN):
                st.session_state.cart = []
                st.session_state.invoice = None
                st.rerun()

# =========================================================
# TAB 2: BÁO CÁO DOANH THU
# =========================================================
with tab_dashboard:
    st.subheader("📈 Thống Kê Doanh Thu & Lịch Sử Bán Hàng")

    all_orders = load_history()   # đọc file chung: thấy cả đơn của người khác
    if not all_orders:
        st.info("Chưa có đơn hàng nào.")
    else:
        df_history = pd.DataFrame(all_orders)

        m1, m2, m3 = st.columns(3)
        m1.metric("Tổng số đơn", f"{len(df_history)} đơn")
        m2.metric("Tổng ly đã bán", f"{int(df_history['total_items'].sum())} ly")
        m3.metric("Tổng doanh thu", f"{int(df_history['final_amount'].sum()):,} VNĐ")

        st.markdown("---")
        st.download_button(
            "📥 Tải báo cáo (.CSV)",
            data=df_history.to_csv(index=False).encode("utf-8-sig"),
            file_name="BaoCao_DoanhThu.csv",
            mime="text/csv",
        )
        st.dataframe(
            df_history.rename(
                columns={
                    "time": "Thời Gian",
                    "customer": "Khách Hàng",
                    "total_items": "Số Ly",
                    "final_amount": "Thành Tiền (VNĐ)",
                }
            ),
            hide_index=True,
            **FULL_DF,
)
