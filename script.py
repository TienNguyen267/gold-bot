import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
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

def seconds_to_next_hour():
    tz = ZoneInfo("Asia/Ho_Chi_Minh")
    now = datetime.now(tz)

    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

    return int((next_hour - now).total_seconds())

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

    await update.message.reply_text("⏰ Auto mỗi giờ (đúng giờ tròn) đã bật")

    # xoá job cũ
    jobs = context.job_queue.jobs()
    for job in jobs:
        if str(chat_id) in job.name:
            job.schedule_removal()

    delay = seconds_to_next_hour()

    # chạy đúng giờ tròn rồi lặp mỗi 1h
    context.job_queue.run_repeating(
        push_gold,
        interval=3600,
        first=delay,
        chat_id=chat_id,
        name=str(chat_id)
    )


# ====== COMMAND /off ======
async def off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    for job in context.job_queue.jobs():
        if str(chat_id) in job.name:
            job.schedule_removal()

    await update.message.reply_text("❌ Đã tắt tất cả auto")


def get_fuel_data():
    try:
        url = "https://www.pvoil.com.vn/tin-gia-xang-dau"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        data = []

        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")

            for row in rows:
                cols = row.find_all("td")

                if len(cols) >= 3:
                    name = cols[1].text.strip()
                    price = cols[2].text.strip()

                    data.append({
                        "name": name,
                        "price": price
                    })

        return data

    except Exception as e:
        print("FUEL error:", e)

    return []


def format_fuel_table(data):
    msg = "⛽ Giá xăng dầu Việt Nam\n\n"

    for i, item in enumerate(data[:5], start=1):
        msg += f"{i}. {item['name']}\n💰 {item['price']}\n\n"

    return msg


async def fuel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_fuel_data()

    if not data:
        await update.message.reply_text("❌ Không lấy được giá xăng")
        return

    now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%d/%m/%Y %H:%M")

    msg = f"🕒 {now}\n\n"
    msg += format_fuel_table(data)

    await update.message.reply_text(msg)

async def auto_gold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    await update.message.reply_text("📊 Đã bật auto giá vàng")

    # xoá job vàng cũ
    for job in context.job_queue.jobs():
        if job.name == f"gold_{chat_id}":
            job.schedule_removal()

    delay = seconds_to_next_hour()

    context.job_queue.run_repeating(
        push_gold_only,
        interval=3600,
        first=delay,
        chat_id=chat_id,
        name=f"gold_{chat_id}"
    )


async def auto_fuel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    await update.message.reply_text("⛽ Đã bật auto giá xăng")

    # xoá job xăng cũ
    for job in context.job_queue.jobs():
        if job.name == f"fuel_{chat_id}":
            job.schedule_removal()

    delay = seconds_to_next_hour()

    context.job_queue.run_repeating(
        push_fuel_only,
        interval=120,
        first=0,
        chat_id=chat_id,
        name=f"fuel_{chat_id}"
    )


async def push_gold_only(context: ContextTypes.DEFAULT_TYPE):
    data = get_gold_table()
    if not data:
        return

    now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%d/%m/%Y %H:%M")

    msg = f"📊 Giá vàng\n🕒 {now}\n\n" + format_gold_table(data)

    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=msg
    )


async def push_fuel_only(context: ContextTypes.DEFAULT_TYPE):
    data = get_fuel_data()
    if not data:
        return

    now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%d/%m/%Y %H:%M")

    msg = f"⛽ Giá xăng dầu\n🕒 {now}\n\n"
    print("RUN GOLD JOB")
    for i, item in enumerate(data[:5], start=1):
        msg += f"{i}. {item['name']} - {item['price']}\n"

    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=msg
    )


# ====== COMMAND /start ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
    "🤖 Bot giá\n\n"
    "📊 /gold → giá vàng\n"
    "⛽ /fuel → giá xăng\n\n"
    "📈 /auto_gold → auto vàng\n"
    "⛽ /auto_fuel → auto xăng\n"
    "❌ /off → tắt tất cả"
)


# ====== MAIN ======
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gold", gold))
    app.add_handler(CommandHandler("auto_gold", auto_gold))
    app.add_handler(CommandHandler("auto_fuel", auto_fuel))
    app.add_handler(CommandHandler("off", off))
    app.add_handler(CommandHandler("fuel", fuel))
    

    print("✅ Bot đang chạy...")
    app.run_polling()


if __name__ == "__main__":
    main()
