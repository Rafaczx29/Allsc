import os
import re
import httpx
import asyncio
from bs4 import BeautifulSoup
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChatAction
)
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# TOKEN BOT TELEGRAM
BOT_TOKEN = "7956681803:AAFwnc47NYn7-83jQUFr42GJajZp_JYFoKM"

# Variabel global untuk menyimpan session dan cookies
user_session = httpx.Client(follow_redirects=True)
cookies = None

# ----------- HANDLE /login ------------
async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Kirim email dan password blacktowhite kamu dalam format:\n\n`email|password`", parse_mode='Markdown')

# ----------- HANDLE CREDENTIAL ------------
async def handle_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cookies

    if '|' not in update.message.text:
        return

    email, password = update.message.text.strip().split("|")
    login_url = "https://www.blacktowhite.net/login/login"

    try:
        response = user_session.post(
            login_url,
            data={"login": email, "password": password}
        )

        if "Log Out" in response.text or "Your Account" in response.text:
            cookies = user_session.cookies
            await update.message.reply_text("Login sukses bro! Sekarang kirim link page medianya (misal: https://blacktowhite.net/media/videos/page-1)")
        else:
            await update.message.reply_text("Login gagal. Cek kembali email/password.")
    except Exception as e:
        await update.message.reply_text(f"Error saat login: {e}")

# ----------- HANDLE LINK PAGE VIDEO ------------
async def handle_media_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cookies

    url = update.message.text.strip()
    chat_id = update.message.chat_id

    if not url.startswith("https://blacktowhite.net/media/videos"):
        return

    await update.message.reply_text("Scraping halaman...")

    try:
        response = user_session.get(url, cookies=cookies)
        soup = BeautifulSoup(response.text, "html.parser")

        video_links = []
        for tag in soup.select("a[data-overlay-url]"):
            href = tag.get("href")
            if href and "/media/" in href:
                video_links.append("https://blacktowhite.net" + href)

        if not video_links:
            await update.message.reply_text("Gagal nemu video di halaman ini.")
            return

        context.user_data['video_links'] = video_links

        # Kirim jumlah & tombol lanjut
        keyboard = [
            [InlineKeyboardButton("Lanjut Download Video", callback_data="download_videos")]
        ]
        await update.message.reply_text(
            f"Ada {len(video_links)} video di halaman ini.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        await update.message.reply_text(f"Error scraping: {e}")

# ----------- HANDLE LANJUT DOWNLOAD ------------
async def download_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cookies
    query = update.callback_query
    await query.answer()

    video_links = context.user_data.get('video_links', [])
    chat_id = query.message.chat_id

    await query.edit_message_text("Mulai download & kirim video...")

    for idx, video_page in enumerate(video_links):
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)

            print(f"[{idx+1}/{len(video_links)}] Ambil: {video_page}")
            page = user_session.get(video_page, cookies=cookies)
            soup = BeautifulSoup(page.text, "html.parser")

            video_tag = soup.find("video")
            if video_tag:
                src = video_tag.find("source").get("src")
                video_url = src if src.startswith("http") else "https:" + src

                # Download video
                filename = f"video_{idx+1}.mp4"
                with httpx.stream("GET", video_url, follow_redirects=True) as r:
                    with open(filename, "wb") as f:
                        for chunk in r.iter_bytes():
                            f.write(chunk)

                # Kirim video ke Telegram
                with open(filename, "rb") as f:
                    await context.bot.send_video(chat_id=chat_id, video=f)

                os.remove(filename)

        except Exception as e:
            await context.bot.send_message(chat_id=chat_id, text=f"Error ambil video {idx+1}: {e}")

# ----------- MAIN APP ------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("login", login_command))
    app.add_handler(CallbackQueryHandler(download_videos, pattern="download_videos"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_credentials))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_media_page))

    print("Bot siap bro! Jalankan dan login dulu pakai /login")
    app.run_polling()

if __name__ == "__main__":
    main()