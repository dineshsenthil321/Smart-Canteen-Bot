from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import datetime
import csv
import os

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

CSV_FILE = "bookings.csv"

# ========= Save New Booking =========
def save_booking(username, item):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode="a", newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Name", "Item", "Time", "Status"])
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([username, item, now, "Booked"])

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
    
    user = query.from_user.first_name
    item = query.data.replace("book_", "")

    save_booking(user, item)
    await query.edit_message_text(f"✅ *{item}* booked successfully!", parse_mode="Markdown")

# ========= /track =========
async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.first_name

    try:
        with open(CSV_FILE, 'r') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            if not rows:
                await update.message.reply_text("❌ No bookings found yet.")
                return
            for row in reversed(rows):
                if row.get("Name") == username:
                    await update.message.reply_text(
                        f"📦 Your last booking:\n"
                        f"Item: *{row.get('Item', 'N/A')}*\n"
                        f"Time: {row.get('Time', 'N/A')}\n"
                        f"Status: *{row.get('Status', 'N/A')}*",
                        parse_mode="Markdown"
                    )
                    return
            await update.message.reply_text("❌ No booking found for you.")
    except FileNotFoundError:
        await update.message.reply_text("⚠️ Booking file not found.")


# ========= /cancel =========
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.first_name
    found = False

    try:
        with open(CSV_FILE, 'r') as file:
            reader = csv.DictReader(file)
            bookings = list(reader)
            headers = reader.fieldnames

        updated_bookings = []
        for row in bookings:
            if row["Name"] == username and row["Status"] == "Booked" and not found:
                row["Status"] = "Cancelled"
                found = True
            updated_bookings.append(row)

        if found:
            with open(CSV_FILE, 'w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=headers)
                writer.writeheader()
                writer.writerows(updated_bookings)
            await update.message.reply_text("✅ Your last booking has been cancelled.")
        else:
            await update.message.reply_text("❌ No active booking found to cancel.")
    except FileNotFoundError:
        await update.message.reply_text("⚠️ Booking file not found.")

# ========= Main =========
def main():
    app = ApplicationBuilder().token("Paste your Bot token here").build()

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
