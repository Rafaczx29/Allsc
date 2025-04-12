import os
import re
import asyncio
import yt_dlp
import httpx
from bs4 import BeautifulSoup
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# === Ganti token bot kalian di bawah ini ===
TOKEN = "7956681803:AAFwnc47NYn7-83jQUFr42GJajZp_JYFoKM"

user_cookies = {}

# Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Kirim /cookie [cookie lengkap] dulu sebelum kirim link halaman media.")

# Command /cookie
async def set_cookie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cookie_text = " ".join(context.args)
    if not cookie_text or "xf_user=" not in cookie_text:
        await update.message.reply_text("Format salah. Kirim seperti ini:\n\n/cookie xf_user=....; xf_session=....; dst")
        return
    user_cookies[user_id] = cookie_text
    await update.message.reply_text("Cookie disimpan. Kirim link halaman media seperti https://www.blacktowhite.net/media/page-2")

# Handler pesan (link halaman media)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_cookies:
        await update.message.reply_text("Cookie belum diatur. Kirim dulu dengan /cookie")
        return

    url = update.message.text.strip()
    if not re.match(r"^https:\/\/www\.blacktowhite\.net\/media\/page-\d+\?type=video", url):
        await update.message.reply_text("Format URL tidak valid. Kirim halaman seperti: https://www.blacktowhite.net/media/page-2?type=video")
        return

    # Ambil semua link video di halaman
    cookie_header = user_cookies[user_id]
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Cookie": cookie_header,
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, headers=headers)
            soup = BeautifulSoup(resp.text, "html.parser")
            # Filter untuk ambil link video yang valid
            links = [
                "https://www.blacktowhite.net" + a["href"]
                for a in soup.select("a[href*='/media/']")
                if a["href"].startswith("/media/") and not a["href"].endswith("add_to_home.mp4")
            ]
    except Exception as e:
        await update.message.reply_text(f"Gagal mengambil link dari halaman: {e}")
        return

    if not links:
        await update.message.reply_text("Tidak ada link video ditemukan di halaman ini.")
        return

    await update.message.reply_text(f"{len(links)} video ditemukan. Mulai download dan kirim satu per satu...")

    for video_link in links:
        try:
            ydl_opts = {
                "outtmpl": "temp.%(ext)s",
                "quiet": True,
                "noplaylist": True,
                "cookiefile": None,
                "http_headers": headers,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_link, download=True)
                file_path = ydl.prepare_filename(info)

            # Mengirim video tanpa menggunakan timeout
            await update.message.reply_video(video=open(file_path, "rb"))
            os.remove(file_path)

        except Exception as e:
            print(f"Gagal download dari {video_link}: {e}")
            continue

# Run bot
if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cookie", set_cookie))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot jalan...")
    app.run_polling()