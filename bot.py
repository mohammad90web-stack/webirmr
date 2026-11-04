import logging
import smtplib
import random
import socket
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# ----------------- توکن ربات -----------------
BOT_TOKEN = "9006387474:AAGbgN7klaGyA4-ms5uEtwxCNtsQBLO-Xo4"

# مراحل گفتگو
NAME, AGE, BIRTH_JALALI, BIRTH_GREGORIAN = range(4)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def check_email_approx(email: str) -> str:
    """چک تقریبی و رایگان ایمیل (دقیق نیست)"""
    try:
        domain = email.split("@")[-1]
        # پیدا کردن سرور میل
        mx_host = f"smtp.{domain}"
        with smtplib.SMTP(timeout=8) as server:
            server.connect(mx_host, 25)
            server.helo(socket.gethostname())
            server.mail("check@test.com")
            code, _ = server.rcpt(email)
            if code == 250:
                return "احتمالاً گرفته شده ❌"
            else:
                return "احتمالاً آزاد ✅"
    except Exception:
        return "نتیجه مشخص نشد ⚠️"


def generate_emails(name: str, age: str, jalali: str, gregorian: str) -> list:
    name_clean = name.lower().replace(" ", "").replace("‌", "")
    year_j = "".join(filter(str.isdigit, jalali))[:4]
    year_g = "".join(filter(str.isdigit, gregorian))[:4]
    short_j = year_j[-2:] if len(year_j) >= 2 else year_j
    short_g = year_g[-2:] if len(year_g) >= 2 else year_g

    candidates = [
        name_clean,
        f"{name_clean}{age}",
        f"{name_clean}{year_j}",
        f"{name_clean}{year_g}",
        f"{name_clean}_{age}",
        f"{name_clean}.{year_g}",
        f"{name_clean}{short_j}",
        f"{name_clean}{short_g}",
        f"{name_clean}{random.randint(10, 99)}",
        f"{name_clean}_{year_g}",
    ]
    # حذف تکراری‌ها و ساخت ایمیل
    unique = list(dict.fromkeys(candidates))
    return [f"{item}@gmail.com" for item in unique[:8]]


def generate_passwords(name: str, age: str, jalali: str, gregorian: str) -> list:
    name_clean = name.replace(" ", "").replace("‌", "")
    year_j = "".join(filter(str.isdigit, jalali))
    year_g = "".join(filter(str.isdigit, gregorian))

    passwords = [
        f"{name_clean}{age}",
        f"{name_clean}{year_j}",
        f"{name_clean}{year_g}",
        f"{name_clean}@{age}",
        f"{name_clean}{year_j[-2:]}",
        f"{name_clean}{random.randint(100, 999)}",
        f"{name_clean.capitalize()}{age}!",
        f"{year_g}{name_clean}",
        f"{name_clean}_{age}",
        f"{name_clean}{age}#",
    ]
    return passwords


# ----------------- هندلرها -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\n"
        "من کمکت می‌کنم چند تا ایمیل و رمز پیشنهادی بر اساس مشخصاتت بسازم.\n\n"
        "لطفاً نام خودت را وارد کن (فارسی یا انگلیسی):",
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("سن خودت را وارد کن (فقط عدد):")
    return AGE


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    age = update.message.text.strip()
    if not age.isdigit():
        await update.message.reply_text("لطفاً فقط عدد وارد کن:")
        return AGE
    context.user_data["age"] = age
    await update.message.reply_text("تاریخ تولد شمسی را وارد کن (مثال: ۱۳۷۸/۰۵/۱۲ یا 1378/05/12):")
    return BIRTH_JALALI


async def get_birth_jalali(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["jalali"] = update.message.text.strip()
    await update.message.reply_text("تاریخ تولد میلادی را وارد کن (مثال: 1999/08/03):")
    return BIRTH_GREGORIAN


async def get_birth_gregorian(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["gregorian"] = update.message.text.strip()

    name = context.user_data["name"]
    age = context.user_data["age"]
    jalali = context.user_data["jalali"]
    gregorian = context.user_data["gregorian"]

    emails = generate_emails(name, age, jalali, gregorian)
    passwords = generate_passwords(name, age, jalali, gregorian)

    # ساخت متن ایمیل‌ها
    email_lines = []
    for email in emails:
        status = check_email_approx(email)
        email_lines.append(f"• {email}\n  └ {status}")

    text = "📧 **ایمیل‌های پیشنهادی:**\n\n"
    text += "\n\n".join(email_lines)
    text += "\n\n────────────────────\n"
    text += "🔑 **رمزهای پیشنهادی:**\n\n"
    text += "\n".join([f"• {p}" for p in passwords])
    text += "\n\n⚠️ توجه: وضعیت ایمیل‌ها تقریبی و غیر دقیق است."

    await update.message.reply_text(text)
    await update.message.reply_text("برای شروع دوباره /start را بزن.")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات لغو شد.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            BIRTH_JALALI: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_birth_jalali)],
            BIRTH_GREGORIAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_birth_gregorian)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("ربات با موفقیت روشن شد...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()