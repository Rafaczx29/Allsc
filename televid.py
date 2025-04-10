from telegram.ext import Updater, MessageHandler, Filters
from telegram import ChatAction
import subprocess
import os

# Ganti dengan token bot kamu dari @BotFather
TOKEN = '7956681803:AAFwnc47NYn7-83jQUFr42GJajZp_JYFoKM'

def download_video(url):
    output = "video.mp4"
    try:
        # Download video kualitas terbaik
        subprocess.run(["yt-dlp", "-f", "best", "-o", output, url], check=True)
        return output
    except:
        return None

def handle_message(update, context):
    chat_id = update.message.chat_id
    url = update.message.text.strip()

    if "http" in url:
        context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)
        update.message.reply_text("Oke bro, tunggu bentar. Lagi ambil videonya...")

        video_file = download_video(url)

        if video_file and os.path.exists(video_file):
            context.bot.send_video(chat_id=chat_id, video=open(video_file, 'rb'))
            os.remove(video_file)
        else:
            update.message.reply_text("Maaf bro, gagal ambil videonya. Link-nya mungkin ga didukung.")
    else:
        update.message.reply_text("Kirim URL yang valid ya bro.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    print("Bot jalan... siap terima link bro!")
    updater.idle()

if __name__ == '__main__':
    main()