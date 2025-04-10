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

    print(f"[INFO] Dapat link: {url}")
    await update.message.reply_text("Tunggu bentar bro, lagi ambil videonya...")

    # Simpan file sebelum download
    files_before = set(os.listdir())

    # Jalankan yt-dlp
    print("[INFO] Proses download video...")
    subprocess.run([
        "yt-dlp", "-f", "best", "-o", "%(title)s.%(ext)s", url
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Ambil file baru
    files_after = set(os.listdir())
    new_files = sorted(list(files_after - files_before), key=os.path.getctime)

    # Filter hanya video
    video_files = [f for f in new_files if f.lower().endswith((".mp4", ".mkv", ".mov"))]
    print(f"[INFO] Ditemukan {len(video_files)} video: {video_files}")

    if len(video_files) < 2:
        await update.message.reply_text("Gagal ambil video utama bro.")
        return

    # Kirim video ke-2 dulu (video utama)
    selected_video = video_files[1]
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)
        with open(selected_video, 'rb') as vid:
            await context.bot.send_video(chat_id=chat_id, video=vid)
            print(f"[KIRIM] Video utama: {selected_video}")
    except Exception as e:
        await update.message.reply_text(f"Error kirim video utama: {e}")
        print(f"[ERROR] Kirim video utama gagal: {e}")

    # Kirim semua video lain (kecuali video utama biar ga double)
    for video in video_files:
        if video == selected_video:
            continue
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)
            with open(video, 'rb') as vid:
                await context.bot.send_video(chat_id=chat_id, video=vid)
                print(f"[KIRIM] Video tambahan: {video}")
        except Exception as e:
            print(f"[ERROR] Kirim video tambahan gagal: {e}")

    # Bersihkan semua video
    for f in video_files:
        os.remove(f)
    print("[INFO] Semua file video dibersihkan.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot aktif bro! Kirim link aja, nanti semua video dikirim otomatis.")
    app.run_polling()