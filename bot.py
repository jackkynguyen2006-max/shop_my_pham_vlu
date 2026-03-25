import sqlite3
import os
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8752531902:AAErY4WzvyJCaFhrAgMu80OvN60GDl-Nc8s"
WEBHOOK_URL = "https://your-app-name.onrender.com"  # đổi thành link Render của bạn

app_web = Flask(__name__)

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
skin_menu = [["Da khô", "Da dầu"], ["Da hỗn hợp", "Da nhạy cảm"]]
skin_markup = ReplyKeyboardMarkup(skin_menu, resize_keyboard=True)

main_menu = [["🧴 Chọn lại loại da"], ["🛒 Giỏ hàng"], ["💳 Thanh toán"]]
main_markup = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)

# --- PRODUCTS ---
products = {
    "Da khô": [
        ("Hydra Cleanser 100k", 100, "💧 Dưỡng ẩm sâu"),
        ("Moist Foam 150k", 150, "🌿 Giữ ẩm"),
        ("Aqua Wash 200k", 200, "💦 Cấp nước"),
        ("Deep Hydrate 250k", 250, "✨ Phục hồi da")
    ],
    "Da dầu": [
        ("Oil Control 300k", 300, "🧼 Kiềm dầu"),
        ("Acne Clean 350k", 350, "🔥 Giảm mụn"),
        ("Sebum Wash 400k", 400, "💨 Làm sạch sâu"),
        ("Pore Clean 450k", 450, "🫧 Se lỗ chân lông")
    ],
    "Da hỗn hợp": [
        ("Balance Clean 500k", 500, "⚖️ Cân bằng da"),
        ("Mix Skin Foam 550k", 550, "🌗 Vùng T"),
        ("Dual Care 600k", 600, "💎 2in1"),
        ("Combo Wash 650k", 650, "🧴 Toàn diện")
    ],
    "Da nhạy cảm": [
        ("Gentle Skin 700k", 700, "🌸 Dịu nhẹ"),
        ("Soft Clean 750k", 750, "🧴 An toàn"),
        ("Calm Wash 800k", 800, "😌 Làm dịu"),
        ("Pure Foam 850k", 850, "🌱 Không kích ứng")
    ]
}

# --- TELEGRAM APP ---
telegram_app = ApplicationBuilder().token(TOKEN).build()

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Chào bạn!\n👉 Chọn loại da:",
        reply_markup=skin_markup
    )

# --- HANDLE ---
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user.full_name

    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    if text in products:
        context.user_data["skin"] = text
        buttons = [[p[0]] for p in products[text]] + [["🔙 Quay lại"]]
        await update.message.reply_text(
            f"✅ {text}\n👉 Chọn sản phẩm:",
            reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
        )

    elif any(text == p[0] for plist in products.values() for p in plist):
        context.user_data["product"] = text

        for plist in products.values():
            for p in plist:
                if p[0] == text:
                    name, price, desc = p

        await update.message.reply_text(
            f"🧴 {name}\n💰 {price}k\n📌 {desc}\n\n👉 Gõ 'Thêm'"
        )

    elif text.lower() == "thêm":
        product = context.user_data.get("product")

        if product:
            for plist in products.values():
                for p in plist:
                    if p[0] == product:
                        price = p[1]

            cursor.execute("INSERT INTO cart (user, product, price) VALUES (?, ?, ?)",
                           (user, product, price))
            conn.commit()

            await update.message.reply_text("✅ Đã thêm!", reply_markup=main_markup)

    elif text == "🛒 Giỏ hàng":
        cursor.execute("SELECT id, product, price FROM cart WHERE user=?", (user,))
        rows = cursor.fetchall()

        if not rows:
            await update.message.reply_text("🛒 Trống!")
        else:
            total = sum(r[2] for r in rows)
            context.user_data["cart"] = rows

            msg = "\n".join([f"{i+1}. {r[1]} - {r[2]}k" for i, r in enumerate(rows)])
            await update.message.reply_text(f"{msg}\n💰 {total}k\n👉 Nhập số để hủy")

    elif text.isdigit():
        cart = context.user_data.get("cart")
        if cart:
            i = int(text) - 1
            if 0 <= i < len(cart):
                cursor.execute("DELETE FROM cart WHERE id=?", (cart[i][0],))
                conn.commit()
                await update.message.reply_text("❌ Đã hủy")

    elif text == "💳 Thanh toán":
        cursor.execute("SELECT SUM(price) FROM cart WHERE user=?", (user,))
        total = cursor.fetchone()[0]

        if total:
            cursor.execute("DELETE FROM cart WHERE user=?", (user,))
            conn.commit()
            await update.message.reply_text(f"🎉 Thành công {total}k")

    elif text == "🔙 Quay lại":
        await update.message.reply_text("👉 Chọn da:", reply_markup=skin_markup)

    conn.close()

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle))

# --- WEBHOOK ROUTE ---
@app_web.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return "OK"

# --- ROOT ---
@app_web.route("/")
def home():
    return "Bot đang chạy!"

# --- START SERVER ---
if __name__ == "__main__":
    import asyncio

    async def main():
        await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")

    asyncio.run(main())

    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)
