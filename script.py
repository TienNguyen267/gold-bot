import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = "8144624079:AAH3Ng1L6Wrth0iYpB4hLK3KxweJNfgzvNU"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "vi-VN,vi;q=0.9"
}

# ====== SCRAPE TABLE ======
def get_gold_table():
    try:
        url = "https://www.24h.com.vn/gia-vang-hom-nay-c425.html"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        data = []
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")

            for row in rows:
                cols = row.find_all("td")

                if len(cols) >= 5:
                    name = cols[0].text.strip()

                    if name and len(name) < 30:
                        data.append({
                            "name": name,
                            "buy": cols[1].text.strip(),
                            "sell": cols[2].text.strip(),
                            "y_buy": cols[3].text.strip(),
                            "y_sell": cols[4].text.strip(),
                        })

        return data

    except Exception as e:
        print("TABLE error:", e)

    return []


# ====== FORMAT ======
def format_gold_table(data):
    msg = "📊 Giá vàng hôm nay 🇻🇳\n\n"

    for item in data[:8]:
        msg += f"""🔸 {item['name']}
💰 {item['buy']} | {item['sell']}
📊 Hôm qua: {item['y_buy']} | {item['y_sell']}

"""
    return msg


# ====== COMMAND /gold ======
async def gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%d/%m/%Y %H:%M")

    data = get_gold_table()

    if not data:
        await update.message.reply_text("❌ Không lấy được dữ liệu")
        return

    msg = f"🕒 {now}\n\n" + format_gold_table(data)

    await update.message.reply_text(msg)


# ====== AUTO PUSH ======
async def push_gold(context: ContextTypes.DEFAULT_TYPE):
    data = get_gold_table()

    if not data:
        return

    now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%d/%m/%Y %H:%M")

    msg = f"⏰ Cập nhật giá vàng\n🕒 {now}\n\n" + format_gold_table(data)

    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=msg
    )


# ====== COMMAND /auto ======
async def auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    await update.message.reply_text("⏰ Đã bật tự động mỗi giờ")

    # xoá job cũ
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

    tz = ZoneInfo("Asia/Ho_Chi_Minh")
    # tạo job mới
    for hour in range(24):
        context.job_queue.run_daily(
            push_gold,
            time=time(hour=hour, minute=0, tzinfo=tz),
            chat_id=chat_id,
            name=f"{chat_id}_{hour}"
        )


# ====== COMMAND /off ======
async def off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()

    await update.message.reply_text("❌ Đã tắt auto")


# ====== COMMAND /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot giá vàng\n\n"
        "📊 /gold → xem giá ngay\n"
        "⏰ /auto → bật tự động mỗi giờ\n"
        "❌ /off → tắt tự động"
    )


# ====== MAIN ======
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gold", gold))
    app.add_handler(CommandHandler("auto", auto))
    app.add_handler(CommandHandler("off", off))

    print("✅ Bot đang chạy...")
    app.run_polling()


if __name__ == "__main__":
    main()
