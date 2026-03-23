import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# TOKEN MỚI CỦA HẢI
TOKEN = "8752531902:AAGTI9UOJogFlqmkuysXT_cRabWZ0ascEG8"

# --- BƯỚC 1: KHỞI TẠO DATABASE (Đúng chuẩn Software Engineering) ---
def init_db():
    conn = sqlite3.connect('my_cosmetic_shop.db')
    cursor = conn.cursor()
    # Tạo bảng lưu đơn hàng: ID, Tên khách, Tên sản phẩm, Thời gian
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       customer_name TEXT, 
                       product_name TEXT,
                       order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# --- BƯỚC 2: CẤU HÌNH MENU ---
menu = [["Da dầu", "Da khô"], ["Xem đơn"]]
markup = ReplyKeyboardMarkup(menu, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.full_name
    await update.message.reply_text(f"Chào {user}! Chọn loại da để mình tư vấn nhé:", reply_markup=markup)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_name = update.message.from_user.full_name

    # Kết nối DB để xử lý
    conn = sqlite3.connect('my_cosmetic_shop.db')
    cursor = conn.cursor()

    if text == "Da dầu":
        context.user_data["product"] = "Sữa rửa mặt CeraVe - 350k"
        await update.message.reply_text("✨ Gợi ý cho da dầu: Sữa rửa mặt CeraVe (350k)\nGõ 'Đặt' để mua ngay!")

    elif text == "Da khô":
        context.user_data["product"] = "Kem dưỡng Neutrogena - 400k"
        await update.message.reply_text("✨ Gợi ý cho da khô: Kem dưỡng Neutrogena (400k)\nGõ 'Đặt' để mua ngay!")

    elif text.lower() == "đặt":
        product = context.user_data.get("product")
        if product:
            # LƯU VÀO DATABASE THẬT (Thay vì list orders = [])
            cursor.execute("INSERT INTO orders (customer_name, product_name) VALUES (?, ?)", (user_name, product))
            conn.commit()
            await update.message.reply_text(f"✅ Chúc mừng {user_name}! Bạn đã đặt thành công: {product}")
        else:
            await update.message.reply_text("⚠️ Bạn chưa chọn sản phẩm nào để đặt cả!")

    elif text == "Xem đơn":
        # TRUY VẤN TỪ DATABASE
        cursor.execute("SELECT product_name FROM orders WHERE customer_name = ?", (user_name,))
        rows = cursor.fetchall()
        
        if not rows:
            await update.message.reply_text("Bạn chưa có đơn hàng nào trong hệ thống.")
        else:
            order_list = "\n".join([f"- {row[0]}" for row in rows])
            await update.message.reply_text(f"🛍️ Các đơn hàng của bạn:\n{order_list}")

    else:
        await update.message.reply_text("Hải ơi, hãy chọn các nút trong Menu bên dưới nhé!")

    conn.close()

# --- BƯỚC 3: KHỞI CHẠY HỆ THỐNG ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, handle))

print("🚀 Bot Tư Vấn Mỹ Phẩm Đang Chạy...")
app.run_polling()