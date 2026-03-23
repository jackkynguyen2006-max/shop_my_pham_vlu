import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8752531902:AAGTI9UOJogFlqmkuysXT_cRabWZ0ascEG8"

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect('my_cosmetic_shop.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       customer_name TEXT, 
                       product_name TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- MENU CHÍNH ---
menu = [
    ["Sữa rửa mặt"],
    ["Xem đơn", "Hủy sản phẩm"]
]
markup = ReplyKeyboardMarkup(menu, resize_keyboard=True)

# --- MENU SẢN PHẨM ---
srm_menu = [
    ["Cetaphil (200k)", "Cosrx (300k)"],
    ["CeraVe (400k)", "La Roche-Posay (500k)"],
    ["Innisfree (600k)"],
    ["Quay lại"]
]
srm_markup = ReplyKeyboardMarkup(srm_menu, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.full_name
    await update.message.reply_text(
        f"👋 Chào {user}!\nChọn sản phẩm bạn muốn mua:",
        reply_markup=markup
    )


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_name = update.message.from_user.full_name

    conn = sqlite3.connect('my_cosmetic_shop.db')
    cursor = conn.cursor()

    # --- CHỌN DANH MỤC ---
    if text == "Sữa rửa mặt":
        await update.message.reply_text(
            "🧴 Chọn sản phẩm:",
            reply_markup=srm_markup
        )

    # --- CHỌN SẢN PHẨM ---
    elif any(x in text for x in ["Cetaphil", "Cosrx", "CeraVe", "La Roche-Posay", "Innisfree"]):
        context.user_data["product"] = text
        await update.message.reply_text(
            f"✅ Bạn đã chọn: {text}\n👉 Gõ 'Đặt' để xác nhận!"
        )

    # --- QUAY LẠI ---
    elif text == "Quay lại":
        await update.message.reply_text("🔙 Menu chính:", reply_markup=markup)

    # --- ĐẶT HÀNG ---
    elif text.lower() == "đặt":
        product = context.user_data.get("product")

        if product:
            cursor.execute(
                "INSERT INTO orders (customer_name, product_name) VALUES (?, ?)",
                (user_name, product)
            )
            conn.commit()

            await update.message.reply_text(
                f"🎉 Đặt thành công: {product}",
                reply_markup=markup
            )
            context.user_data["product"] = None
        else:
            await update.message.reply_text("⚠️ Bạn chưa chọn sản phẩm!")

    # --- XEM ĐƠN ---
    elif text == "Xem đơn":
        cursor.execute(
            "SELECT id, product_name FROM orders WHERE customer_name = ?",
            (user_name,)
        )
        rows = cursor.fetchall()

        if not rows:
            await update.message.reply_text("🛒 Bạn chưa có đơn nào.")
        else:
            order_list = "\n".join(
                [f"{i+1}. {row[1]}" for i, row in enumerate(rows)]
            )
            context.user_data["orders"] = rows

            await update.message.reply_text(
                f"📦 Đơn hàng của bạn:\n{order_list}\n\n👉 Nhập số để hủy sản phẩm"
            )

    # --- HỦY THEO SỐ ---
    elif text.isdigit():
        orders = context.user_data.get("orders")

        if orders:
            index = int(text) - 1
            if 0 <= index < len(orders):
                order_id = orders[index][0]

                cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
                conn.commit()

                await update.message.reply_text("❌ Đã hủy sản phẩm thành công!")
            else:
                await update.message.reply_text("⚠️ Số không hợp lệ!")
        else:
            await update.message.reply_text("⚠️ Bạn chưa xem đơn để hủy!")

    # --- NÚT HỦY ---
    elif text == "Hủy sản phẩm":
        await update.message.reply_text(
            "👉 Vào 'Xem đơn' rồi nhập số thứ tự sản phẩm để hủy"
        )

    else:
        await update.message.reply_text("👉 Hãy chọn bằng nút!", reply_markup=markup)

    conn.close()


# --- CHẠY BOT ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle))

print("🚀 Bot đã chạy phiên bản mới!")
app.run_polling()
