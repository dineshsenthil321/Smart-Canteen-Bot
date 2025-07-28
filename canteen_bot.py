from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import datetime
import mysql.connector

# ========= MySQL Booking Save Function =========
def save_booking(username, item):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="enter your password",
            database="smart_canteen"
        )
        cursor = conn.cursor()
        query = "INSERT INTO bookings (username, item, status) VALUES (%s, %s, %s)"
        values = (username, item, "Booked")
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        print(f"[✅ SAVED] {username} booked {item}")
    except mysql.connector.Error as error:
        print("[❌ ERROR] saving booking:", error)

# ========= Fetch Last Booking =========
def get_last_booking(username):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234567890",
            database="smart_canteen"
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM bookings 
            WHERE username = %s 
            ORDER BY id DESC 
            LIMIT 1
        """, (username,))
        booking = cursor.fetchone()
        cursor.close()
        conn.close()
        return booking
    except mysql.connector.Error as error:
        print("Error fetching booking:", error)
        return None

# ========= Cancel Last Booking =========
def cancel_last_booking(username):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="enter your password",
            database="smart_canteen"
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM bookings 
            WHERE username = %s AND status = 'Booked' 
            ORDER BY id DESC 
            LIMIT 1
        """, (username,))
        booking = cursor.fetchone()
        if booking:
            cursor.execute("UPDATE bookings SET status = 'Cancelled' WHERE id = %s", (booking["id"],))
            conn.commit()
            result = True
        else:
            result = False
        cursor.close()
        conn.close()
        return result
    except mysql.connector.Error as error:
        print("Error cancelling booking:", error)
        return False

# ========= Menu by Day =========
menu_data = {
    "Monday": ["Idli", "Vada", "Pongal"],
    "Tuesday": ["Dosa", "Poori", "Upma"],
    "Wednesday": ["Chapati", "Sambar Rice", "Curd Rice"],
    "Thursday": ["Parotta", "Idiyappam", "Tomato Rice"],
    "Friday": ["Lemon Rice", "Veg Biryani", "Pasta"],
    "Saturday": ["Chole Bhature", "Poha", "Khichdi"],
    "Sunday": ["Special Meals", "Fried Rice", "Noodles"]
}

# ========= /start =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Smart Canteen Bot!\n\n"
        "Use /menu to view today's menu.\n"
        "Use /book to pre-book your meal.\n"
        "Use /track to check your booking.\n"
        "Use /cancel to cancel your booking."
    )

# ========= /menu =========
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = datetime.datetime.today().strftime("%A")
    today_menu = menu_data.get(day, ["Menu not available"])
    menu_str = "\n".join([f"🍽️ {item}" for item in today_menu])
    await update.message.reply_text(f"📅 *{day}* Menu:\n{menu_str}", parse_mode="Markdown")

# ========= /book =========
async def book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = datetime.datetime.today().strftime("%A")
    today_menu = menu_data.get(day, [])
    if not today_menu:
        await update.message.reply_text("⚠️ No menu available for today.")
        return
    buttons = [[InlineKeyboardButton(text=item, callback_data=f"book_{item}")] for item in today_menu]
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("🍽️ Choose your meal to pre-book:", reply_markup=keyboard)

# ========= Button Callback =========
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user.username or query.from_user.first_name
    item = query.data.replace("book_", "")

    save_booking(user, item)
    await query.edit_message_text(f"✅ *{item}* booked successfully!", parse_mode="Markdown")

# ========= /track =========
async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username or update.effective_user.first_name
    booking = get_last_booking(username)
    if booking:
        await update.message.reply_text(
            f"📦 Your last booking:\n"
            f"Item: *{booking['item']}*\n"
            f"Time: {booking['time'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Status: *{booking['status']}*",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ No booking found.")

# ========= /cancel =========
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username or update.effective_user.first_name
    success = cancel_last_booking(username)
    if success:
        await update.message.reply_text("✅ Your last booking has been cancelled.")
    else:
        await update.message.reply_text("❌ No active booking found to cancel.")

# ========= Main =========
def main():
    app = ApplicationBuilder().token("paste your token").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("book", book))
    app.add_handler(CommandHandler("track", track))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(handle_button))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
