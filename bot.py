import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# TOKEN CỦA HẢI (Giữ nguyên)
TOKEN = "8752531902:AAGTI9UOJogFlqmkuysXT_cRabWZ0ascEG8"

# --- BƯỚC 1: KHỞI TẠO DATABASE ---
def init_db():
    conn = sqlite3.connect('my_cosmetic_shop.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       customer_name TEXT, 
                       product_name TEXT,
                       order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# --- BƯỚC 2: CẤU HÌNH MENU MỚI ---
# Thêm nút "Hủy đơn" vào menu chính
menu = [["Sữa rửa mặt", "Kem dưỡng"], ["Xem đơn", "Hủy đơn"]]
markup = ReplyKeyboardMarkup(menu, resize_keyboard=True)

# Menu riêng cho Sữa rửa mặt (Hãng nổi tiếng)
srm_menu = [["La Roche-Posay (450k)", "Cosrx (250k)"], ["CeraVe (350k)", "Quay lại"]]
srm_markup = ReplyKeyboardMarkup(srm_menu, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.full_name
    await update.message.reply_text(f"Chào {user}! Bạn cần tìm sản phẩm gì?", reply_markup=markup)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_name = update.message.from_user.full_name
    conn = sqlite3.connect('my_cosmetic_shop.db')
    cursor = conn.cursor()

    # 1. Chọn danh mục Sữa rửa mặt
    if text == "Sữa rửa mặt":
        await update.message.reply_text("Chọn hãng sữa rửa mặt bạn yêu thích:", reply_markup=srm_markup)

    # 2. Xử lý khi chọn các hãng cụ thể
    elif any(brand in text for brand in ["La Roche-Posay", "Cosrx", "CeraVe"]):
        context.user_data["product"] = text
        await update.message.reply_text(f"✨ Lựa chọn tuyệt vời! Bạn chọn: {text}\nGõ 'Đặt' để xác nhận mua nhé!")

    # 3. Quay lại menu chính
    elif text == "Quay lại":
        await update.message.reply_text("Quay lại menu chính:", reply_markup=markup)

    # 4. Xử lý ĐẶT HÀNG
    elif text.lower() == "đặt":
        product = context.user_data.get("product")
        if product:
            cursor.execute("INSERT INTO orders (customer_name, product_name) VALUES (?, ?)", (user_name, product))
            conn.commit()
            await update.message.reply_text(f"✅ Chúc mừng {user_name}! Đã đặt thành công: {product}", reply_markup=markup)
            context.user_data["product"] = None # Xóa nhớ tạm sau khi đặt
        else:
            await update.message.reply_text("⚠️ Bạn chưa chọn món nào. Hãy chọn Sữa rửa mặt trước nhé!")

    # 5. Xử lý XEM ĐƠN
    elif text == "Xem đơn":
        cursor.execute("SELECT product_name FROM orders WHERE customer_name = ?", (user_name,))
        rows = cursor.fetchall()
        if not rows:
            await update.message.reply_text("Giỏ hàng của bạn đang trống.")
        else:
            order_list = "\n".join([f"- {row[0]}" for row in rows])
            await update.message.reply_text(f"🛍️ Các đơn hàng đã lưu của bạn:\n{order_list}")

    # 6. Xử lý HỦY ĐƠN (Tính năng mới Hải yêu cầu)
    elif text == "Hủy đơn":
        # Xóa đơn hàng cuối cùng của người dùng này
        cursor.execute("DELETE FROM orders WHERE id = (SELECT MAX(id) FROM orders WHERE customer_name = ?)", (user_name,))
        conn.commit()
        if conn.total_changes > 0:
            await update.message.reply_text("❌ Đã hủy sản phẩm bạn vừa đặt gần nhất!")
        else:
            await update.message.reply_text("Bạn không có đơn nào để hủy cả.")

    else:
        await update.message.reply_text("Hải ơi, hãy dùng các nút bấm để chọn nhé!", reply_markup=markup)

    conn.close()

# --- BƯỚC 3: CHẠY BOT ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle))

print("🚀 Bot đã cập nhật tính năng Hủy & Sản phẩm mới!")
app.run_polling()
