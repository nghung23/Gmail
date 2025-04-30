import logging
from telegram import Update, Message
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from datetime import datetime, timedelta

# --- CẤU HÌNH ---
BOT_TOKEN = '7759254055:AAGrwcbXaClF_iJG1VuKa43JtXmeA45tY1Y'  # Thay bằng token bot của bạn
ADMIN_CHAT_ID = 5529113729    # Telegram ID của admin
GROUP_CHAT_ID = -1002557003660  # ID nhóm

# --- BIẾN TẠM ---
user_message_map = {}      # Lưu: message_id gửi admin => user_id
known_users = set()        # Tập hợp user_id đã dùng bot

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    known_users.add(update.message.from_user.id)
    await update.message.reply_text(
        "Chào bạn đến với bot nộp Gmail tự động!\nDùng lệnh /mail để bắt đầu."
    )

# --- /mail ---
async def mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    lines = text.strip().split('\n')
    known_users.add(update.message.from_user.id)

    if len(lines) < 6:
        await update.message.reply_text(
            "Vui lòng gửi nội dung theo định dạng:\n\n"
            "1. NGUYEN VAN A\n"
            "2. Tên ngân hàng + STK\n"
            "3. Mk: minhtu99@\n"
            "4. Ngày: (tự động)\n"
            "5. Tổng: (tự động)\n"
            "thihoan9272@gmail.com\n"
            "nguyenhoang8264@gmail.com\n"
            "anhtu27383@gmail.com\n"
        )
        return

    try:
        name = lines[1].split('1. ')[-1].strip()
        bank = lines[2].split('2. ')[-1].strip()
        password = lines[3].split('3. ')[-1].strip()

        # Giờ Việt Nam
        vietnam_time = datetime.utcnow() + timedelta(hours=7)
        date_str = vietnam_time.strftime("%d/%m/%Y %H:%M:%S")

        gmails = [line.strip() for line in lines[6:] if '@' in line]
        total = len(gmails)

        if total == 0:
            await update.message.reply_text("Không có Gmail nào được gửi.")
            return

        username = update.message.from_user.username or update.message.from_user.first_name
        user_id = update.message.from_user.id

        # Gửi nhóm
        group_msg = f"@{username}\n4. Ngày: {date_str}\n5. Tổng: {total} Gmail"
        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=group_msg)

        # Gửi admin
        admin_text = (
            f"@{username}\n"
            f"1. {name}\n"
            f"2. {bank}\n"
            f"3. {password}\n"
            f"4. Ngày: {date_str}\n"
            f"5. Tổng: {total}\n\n"
            + "\n".join(gmails)
        )
        sent_msg: Message = await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text)

        user_message_map[sent_msg.message_id] = {
            "user_id": user_id,
            "text": admin_text
        }

        await update.message.reply_text("Đã nộp Gmail thành công!")

    except Exception as e:
        logging.error(e)
        await update.message.reply_text("Đã xảy ra lỗi. Vui lòng kiểm tra lại định dạng.")

# --- ADMIN PHẢN HỒI DONE ---
async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_CHAT_ID:
        return

    if update.message.reply_to_message:
        original_msg_id = update.message.reply_to_message.message_id

        if original_msg_id in user_message_map:
            user_data = user_message_map[original_msg_id]
            user_id = user_data["user_id"]
            content = user_data["text"]

            await context.bot.send_message(chat_id=user_id, text=f"{content}\n\n✅ Done!")

# --- ADMIN GỬI THÔNG BÁO ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_CHAT_ID:
        return

    if not context.args:
        await update.message.reply_text("Dùng lệnh: /broadcast Nội_dung_thông_báo")
        return

    message = " ".join(context.args)
    count = 0

    for user_id in known_users:
        try:
            await context.bot.send_message(chat_id=user_id, text=f"**[Thông báo từ admin]**\n\n{message}")
            count += 1
        except Exception as e:
            logging.warning(f"Không gửi được cho user {user_id}: {e}")

    await update.message.reply_text(f"Đã gửi thông báo cho {count} người dùng.")

# --- MAIN ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^/mail"), mail))
    app.add_handler(MessageHandler(filters.REPLY & filters.TEXT, handle_reply))
    app.run_polling()

if __name__ == "__main__":
    main()
