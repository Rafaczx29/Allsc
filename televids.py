import os
import subprocess
from telegram import Update, ChatAction
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = "7956681803:AAFwnc47NYn7-83jQUFr42GJajZp_JYFoKM"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.message.chat_id

    await update.message.reply_text("Ambil video dulu bro, tunggu sebentar...")

    # Simpan daftar file sebelum download
    files_before = set(os.listdir())

    # Jalankan yt-dlp untuk ambil video
    subprocess.run(
        ["yt-dlp", "-f", "bestvideo+bestaudio/best", "-o", "%(title)s.%(ext)s", url],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Daftar file setelah download
    files_after = set(os.listdir())
    new_files = sorted(list(files_after - files_before), key=os.path.getctime)

    # Filter hanya file video
    video_files = [f for f in new_files if f.lower().endswith((".mp4", ".mkv", ".mov"))]

    if len(video_files) < 2:
        await update.message.reply_text("Gagal ambil video utamanya bro. Coba cek link-nya.")
        return

    # Ambil video ke-2 (yang utama)
    vid = video_files[1]  # urutan kedua (index 1)

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)
    with open(vid, 'rb') as f:
        await context.bot.send_video(chat_id=chat_id, video=f)

    # Hapus semua video yang diunduh (bersih-bersih)
    for v in video_files:
        os.remove(v)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot aktif bro! Kirim link dan video ke-2 bakal langsung dikirim.")
    app.run_polling()