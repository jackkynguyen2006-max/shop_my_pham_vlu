import sqlite3
import os
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- CẤU HÌNH WEB SERVER (FLASK) ---
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot is running!"

def run_web():
    # Render sử dụng cổng 10000 mặc định cho Web Service
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host="0.0.0.0", port=port)

# --- TELEGRAM BOT LOGIC ---
TOKEN = "8752531902:AAErY4WzvyJCaFhrAgMu80OvN60GDl-Nc8s"

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

# (Các menu và sản phẩm giữ nguyên như code của bạn)
skin_menu = [["Da khô", "Da dầu"], ["Da hỗn hợp", "Da nhạy cảm"]]
skin_markup = ReplyKeyboardMarkup(skin_menu, resize_keyboard=True)
main_menu = [["🧴 Chọn lại loại da"], ["🛒 Giỏ hàng"], ["💳 Thanh toán"]]
main_markup = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)

products = {
    "Da khô": [("Hydra Cleanser 100k", 100), ("Moist Foam 150k", 150), ("Aqua Wash 200k", 200), ("Deep Hydrate 250k", 250)],
    "Da dầu": [("Oil Control 300k", 300), ("Acne Clean 350k", 350), ("Sebum Wash 400k", 400), ("Pore Clean 450k", 450)],
    "Da hỗn hợp": [("Balance Clean 500k", 500), ("Mix Skin Foam 550k", 550), ("Dual Care 600k", 600), ("Combo Wash 650k", 650)],
    "Da nhạy cảm": [("Gentle Skin 700k", 700), ("Soft Clean 750k", 750), ("Calm Wash 800k", 800), ("Pure Foam 850k", 850)]
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Chào bạn!\n👉 Chọn loại da của bạn:", reply_markup=skin_markup)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user.full_name
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    if text in products:
        context.user_data["skin"] = text
        product_buttons = [[p[0]] for p in products[text]]
        product_buttons.append(["🔙 Quay lại"])
        await update.message.reply_text(f"✅ Bạn chọn {text}\n👉 Chọn sữa rửa mặt:", reply_markup=ReplyKeyboardMarkup(product_buttons, resize_keyboard=True))
    
    elif any(text == p[0] for plist in products.values() for p in plist):
        context.user_data["product"] = text
        await update.message.reply_text(f"🧴 {text}\n👉 Gõ 'Thêm' để thêm vào giỏ")

    elif text.lower() == "thêm":
        product = context.user_data.get("product")
        if product:
            price = next(p[1] for plist in products.values() for p in plist if p[0] == product)
            cursor.execute("INSERT INTO cart (user, product, price) VALUES (?, ?, ?)", (user, product, price))
            conn.commit()
            await update.message.reply_text("✅ Đã thêm vào giỏ!", reply_markup=main_markup)
        else:
            await update.message.reply_text("⚠️ Chọn sản phẩm trước!")

    elif text == "🛒 Giỏ hàng":
        cursor.execute("SELECT id, product, price FROM cart WHERE user=?", (user,))
        rows = cursor.fetchall()
        if not rows:
            await update.message.reply_text("🛒 Giỏ trống!")
        else:
            total = sum(r[2] for r in rows)
            context.user_data["cart"] = rows
            msg = "\n".join([f"{i+1}. {r[1]} - {r[2]}k" for i, r in enumerate(rows)])
            await update.message.reply_text(f"🛒 Giỏ hàng:\n{msg}\n\n💰 Tổng: {total}k\n👉 Nhập số để hủy")

    elif text.isdigit():
        cart = context.user_data.get("cart")
        if cart:
            i = int(text) - 1
            if 0 <= i < len(cart):
                cursor.execute("DELETE FROM cart WHERE id=?", (cart[i][0],))
                conn.commit()
                await update.message.reply_text("❌ Đã hủy sản phẩm!")
            else:
                await update.message.reply_text("⚠️ Số không hợp lệ!")
        else:
            await update.message.reply_text("⚠️ Vào giỏ trước!")

    elif text == "💳 Thanh toán":
        cursor.execute("SELECT SUM(price) FROM cart WHERE user=?", (user,))
        total = cursor.fetchone()[0]
        if total:
            cursor.execute("DELETE FROM cart WHERE user=?", (user,))
            conn.commit()
            await update.message.reply_text(f"🎉 Thanh toán thành công!\n💰 Tổng: {total}k")
        else:
            await update.message.reply_text("Giỏ trống!")

    elif text == "🔙 Quay lại" or text == "🧴 Chọn lại loại da":
        await update.message.reply_text("👉 Chọn lại loại da:", reply_markup=skin_markup)
    else:
        await update.message.reply_text("👉 Hãy chọn bằng nút!")

    conn.close()

# --- CHẠY BOT ---
if __name__ == "__main__":
    # 1. Khởi chạy Flask trong một luồng riêng
    threading.Thread(target=run_web, daemon=True).start()
    print("🌍 Web server mồi đã khởi động...")

    # 2. Khởi chạy Telegram Bot
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle))

    print("🔥 Bot skincare đang chạy...")
    app.run_polling()
