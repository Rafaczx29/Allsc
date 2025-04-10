import os
import subprocess
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# Ganti dengan token bot kamu
BOT_TOKEN = "7956681803:AAFwnc47NYn7-83jQUFr42GJajZp_JYFoKM"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.message.chat_id

    await update.message.reply_text("Tunggu bentar bro, lagi ambil videonya...")

    # Simpan file sebelum download
    files_before = set(os.listdir())

    # Jalankan yt-dlp
    subprocess.run([
        "yt-dlp", "-f", "best", "-o", "%(title)s.%(ext)s", url
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Ambil file baru
    files_after = set(os.listdir())
    new_files = sorted(list(files_after - files_before), key=os.path.getctime)

    # Filter hanya video
    video_files = [f for f in new_files if f.lower().endswith((".mp4", ".mkv", ".mov"))]

    if len(video_files) < 2:
        await update.message.reply_text("Gagal ambil video utama bro.")
        return

    # Ambil video ke-2 (biasanya isi utama)
    selected_video = video_files[1]

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)

    try:
        with open(selected_video, 'rb') as vid:
            await context.bot.send_video(chat_id=chat_id, video=vid)
    except Exception as e:
        await update.message.reply_text(f"Error kirim video: {e}")

    # Bersihkan file
    for f in video_files:
        os.remove(f)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot aktif bro! Kirim link aja, nanti video ke-2 dikirim otomatis.")
    app.run_polling()