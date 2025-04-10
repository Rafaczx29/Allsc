import os
import subprocess
from telegram import ChatAction
from telegram.ext import Updater, MessageHandler, Filters
import yt_dlp

# Token bot Telegram kamu
TELEGRAM_BOT_TOKEN = '7956681803:AAFwnc47NYn7-83jQUFr42GJajZp_JYFoKM'

def download_videos(url):
    output_files = []
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video_%(autonumber)03d.%(ext)s',
        'noplaylist': False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        if 'entries' in info:
            for idx, entry in enumerate(info['entries']):
                ext = entry.get('ext', 'mp4')
                filename = f"video_{idx+1:03d}.{ext}"
                output_files.append(filename)
        else:
            ext = info.get('ext', 'mp4')
            filename = f"video_001.{ext}"
            output_files.append(filename)

    return output_files

def handle_message(update, context):
    url = update.message.text.strip()
    chat_id = update.message.chat_id

    update.message.reply_text("Tunggu bentar bro, lagi ambil videonya...")

    try:
        videos = download_videos(url)

        for vid in videos:
            if os.path.exists(vid):
                # Resize video agar sesuai rasio standar (1280x720)
                resized_file = f"resized_{vid}"
                subprocess.run(["ffmpeg", "-i", vid, "-vf", "scale=1280:720", "-c:a", "copy", resized_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)
                with open(resized_file, 'rb') as vfile:
                    context.bot.send_video(chat_id=chat_id, video=vfile)

                os.remove(vid)
                os.remove(resized_file)

        if not videos:
            update.message.reply_text("Gagal ambil video bro.")
    except Exception as e:
        update.message.reply_text(f"Error saat download: {e}")

def main():
    print("Bot sudah jalan bro, kirim link ke Telegram ya...")
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()