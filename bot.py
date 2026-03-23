import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8752531902:AAGTI9UOJogFlqmkuysXT_cRabWZ0ascEG8"

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS cart 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       user TEXT,
                       product TEXT,
                       price INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- MENU ---
menu = [
    ["🧴 Sữa rửa mặt"],
    ["🛒 Xem giỏ", "❌ Hủy sản phẩm"],
    ["💳 Thanh toán"]
]
markup = ReplyKeyboardMarkup(menu, resize_keyboard=True)

# --- SẢN PHẨM ---
products = {
    "Cetaphil": {"price": 200, "desc": "🌿 Dịu nhẹ, da nhạy cảm", "img": "https://i.imgur.com/1.jpg"},
    "Cosrx": {"price": 300, "desc": "✨ Giảm mụn, da dầu", "img": "https://i.imgur.com/2.jpg"},
    "CeraVe": {"price": 400, "desc": "💧 Cấp ẩm, phục hồi da", "img": "https://i.imgur.com/3.jpg"},
    "La Roche-Posay": {"price": 500, "desc": "🧼 Da dầu mụn", "img": "https://i.imgur.com/4.jpg"},
    "Innisfree": {"price": 600, "desc": "🍃 Thiên nhiên", "img": "https://i.imgur.com/5.jpg"},
    "Simple": {"price": 250, "desc": "🌱 Không kích ứng", "img": "https://i.imgur.com/6.jpg"},
    "Senka": {"price": 350, "desc": "🫧 Sạch sâu", "img": "https://i.imgur.com/7.jpg"},
}

# menu sản phẩm
product_buttons = [[f"{name} ({info['price']}k)"] for name, info in products.items()]
product_buttons.append(["🔙 Quay lại"])
product_markup = ReplyKeyboardMarkup(product_buttons, resize_keyboard=True)

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Chào bạn! Chọn sản phẩm:", reply_markup=markup)

# --- HANDLE ---
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user.full_name

    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    # --- MỞ MENU ---
    if text == "🧴 Sữa rửa mặt":
        await update.message.reply_text("Chọn sản phẩm:", reply_markup=product_markup)

    # --- CHỌN SẢN PHẨM ---
    elif any(name in text for name in products):
        for name in products:
            if name in text:
                p = products[name]
                context.user_data["product"] = name

                await update.message.reply_photo(
                    photo=p["img"],
                    caption=f"🧴 {name}\n💰 {p['price']}k\n{p['desc']}\n\n👉 Gõ 'Thêm' để thêm vào giỏ"
                )

    # --- THÊM GIỎ ---
    elif text.lower() == "thêm":
        name = context.user_data.get("product")

        if name:
            price = products[name]["price"]
            cursor.execute("INSERT INTO cart (user, product, price) VALUES (?, ?, ?)",
                           (user, name, price))
            conn.commit()

            await update.message.reply_text(f"✅ Đã thêm {name} vào giỏ!")
        else:
            await update.message.reply_text("⚠️ Chọn sản phẩm trước!")

    # --- XEM GIỎ ---
    elif text == "🛒 Xem giỏ":
        cursor.execute("SELECT id, product, price FROM cart WHERE user=?", (user,))
        rows = cursor.fetchall()

        if not rows:
            await update.message.reply_text("🛒 Giỏ trống!")
        else:
            total = sum(r[2] for r in rows)
            msg = "\n".join([f"{i+1}. {r[1]} - {r[2]}k" for i, r in enumerate(rows)])

            context.user_data["cart"] = rows

            await update.message.reply_text(
                f"🛒 Giỏ hàng:\n{msg}\n\n💰 Tổng: {total}k\n👉 Nhập số để hủy"
            )

    # --- HỦY ---
    elif text.isdigit():
        cart = context.user_data.get("cart")

        if cart:
            i = int(text) - 1
            if 0 <= i < len(cart):
                cursor.execute("DELETE FROM cart WHERE id=?", (cart[i][0],))
                conn.commit()
                await update.message.reply_text("❌ Đã xóa sản phẩm!")
            else:
                await update.message.reply_text("Sai số!")
        else:
            await update.message.reply_text("Vào giỏ trước!")

    # --- THANH TOÁN ---
    elif text == "💳 Thanh toán":
        cursor.execute("SELECT SUM(price) FROM cart WHERE user=?", (user,))
        total = cursor.fetchone()[0]

        if total:
            cursor.execute("DELETE FROM cart WHERE user=?", (user,))
            conn.commit()
            await update.message.reply_text(f"🎉 Thanh toán thành công!\n💰 Tổng: {total}k")
        else:
            await update.message.reply_text("Giỏ trống!")

    # --- QUAY LẠI ---
    elif text == "🔙 Quay lại":
        await update.message.reply_text("Menu chính:", reply_markup=markup)

    else:
        await update.message.reply_text("👉 Dùng nút nhé!", reply_markup=markup)

    conn.close()

# --- RUN ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle))

print("🔥 Bot version PRO đang chạy...")
app.run_polling()
