import os
import subprocess
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = "7956681803:AAFwnc47NYn7-83jQUFr42GJajZp_JYFoKM"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.message.chat_id

    await update.message.reply_text("📥 Tunggu bentar bro, lagi ambil videonya...")

    # Simpan file sebelum download
    files_before = set(os.listdir())

    # Jalankan yt-dlp
    subprocess.run([
        "yt-dlp", "-f", "best", "-o", "%(title)s.%(ext)s", url
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Ambil file baru
    files_after = set(os.listdir())
    new_files = sorted(list(files_after - files_before), key=os.path.getctime)

    # Filter hanya file video
    video_files = [f for f in new_files if f.lower().endswith((".mp4", ".mkv", ".mov"))]

    if len(video_files) < 2:
        await update.message.reply_text("⚠️ Gagal ambil video utama bro.")
        return

    selected_video = video_files[1]
    file_size = os.path.getsize(selected_video)

    # Info ke user
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)

    try:
        if file_size > 2 * 1024 * 1024 * 1024:  # lebih dari 2GB
            await update.message.reply_text("❌ File terlalu besar (>2GB), gak bisa dikirim.")
        else:
            with open(selected_video, 'rb') as vid:
                await context.bot.send_document(chat_id=chat_id, document=vid)
    except Exception as e:
        await update.message.reply_text(f"❌ Error kirim video: {e}")

    # Bersihkan file lokal
    for f in video_files:
        os.remove(f)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot aktif bro! Kirim link aja, nanti video ke-2 dikirim otomatis.")
    app.run_polling()