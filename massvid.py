import os
import re
import httpx
import asyncio
from bs4 import BeautifulSoup
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
from telegram.constants import ChatAction

BOT_TOKEN = "7956681803:AAFwnc47NYn7-83jQUFr42GJajZp_JYFoKM"
user_session = httpx.Client(follow_redirects=True)
cookies = None
user_id_logged_in = None
stored_url = None

# ---- LOGIN COMMAND ----
async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Kirim email dan password Blacktowhite kamu dalam format:\n\n`email@domain.com|password`", parse_mode="Markdown")

# ---- HANDLE CREDENTIAL ----
async def handle_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cookies, user_id_logged_in
    if "|" not in update.message.text:
        return
    email, password = update.message.text.strip().split("|")
    login_url = "https://www.blacktowhite.net/login/login"

    try:
        res = user_session.post(login_url, data={"login": email, "password": password})
        if "Log Out" in res.text or "Your Account" in res.text:
            cookies = user_session.cookies
            user_id_logged_in = update.message.from_user.id
            await update.message.reply_text("Login sukses bro! Sekarang kirim link halaman video.")
        else:
            await update.message.reply_text("Login gagal. Cek kembali email/password.")
    except Exception as e:
        await update.message.reply_text(f"Gagal login: {e}")

# ---- HANDLE LINK PAGE ----
async def handle_page_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global stored_url

    if update.message.from_user.id != user_id_logged_in:
        await update.message.reply_text("Login dulu bro pakai /login.")
        return

    url = update.message.text.strip()
    if not url.startswith("https://blacktowhite.net/media/videos/"):
        await update.message.reply_text("Link tidak valid. Harus dari halaman video Blacktowhite.")
        return

    stored_url = url
    try:
        res = user_session.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        video_links = soup.find_all("a", href=re.compile(r"^/media/[^/]+/"))

        await update.message.reply_text(
            f"Ditemukan {len(video_links)} video di halaman ini.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Lanjut Download", callback_data="download_videos")]
            ])
        )
    except Exception as e:
        await update.message.reply_text(f"Gagal scrape halaman: {e}")

# ---- HANDLE BUTTON "Lanjut" ----
async def download_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global stored_url
    query = update.callback_query
    await query.answer()

    await context.bot.send_message(chat_id=query.from_user.id, text="Proses ambil video dimulai bro...")

    res = user_session.get(stored_url)
    soup = BeautifulSoup(res.text, "html.parser")
    video_links = soup.find_all("a", href=re.compile(r"^/media/[^/]+/"))

    media_urls = ["https://blacktowhite.net" + a['href'] for a in video_links]

    for idx, media_url in enumerate(media_urls):
        await context.bot.send_message(chat_id=query.from_user.id, text=f"Download video {idx + 1}/{len(media_urls)}")

        # Simpan file sebelum download
        before = set(os.listdir())

        try:
            os.system(f'yt-dlp -f best -o "%(title)s.%(ext)s" "{media_url}" > /dev/null 2>&1')
        except:
            continue

        after = set(os.listdir())
        new_files = list(after - before)
        video_files = [f for f in new_files if f.lower().endswith((".mp4", ".mkv", ".mov"))]

        for vid in sorted(video_files, key=os.path.getctime):
            await context.bot.send_chat_action(chat_id=query.from_user.id, action=ChatAction.UPLOAD_VIDEO)
            try:
                with open(vid, 'rb') as v:
                    await context.bot.send_video(chat_id=query.from_user.id, video=v)
            except Exception as e:
                await context.bot.send_message(chat_id=query.from_user.id, text=f"Gagal kirim: {e}")
            os.remove(vid)

    await context.bot.send_message(chat_id=query.from_user.id, text="Selesai semua bro!")

# ---- MAIN ----
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("login", login_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_credentials))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_page_link))
    app.add_handler(CallbackQueryHandler(download_videos, pattern="download_videos"))

    print("Bot jalan bro... tinggal kirim /login dulu.")
    app.run_polling()

if __name__ == "__main__":
    main()