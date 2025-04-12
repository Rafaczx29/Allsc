import httpx
from bs4 import BeautifulSoup
from telegram import (Update, InlineKeyboardMarkup, InlineKeyboardButton, ChatAction)
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# TOKEN BOT TELEGRAM
BOT_TOKEN = "7956681803:AAFwnc47NYn7-83jQUFr42GJajZp_JYFoKM"  # Ganti dengan token bot Telegram kamu

# Global session untuk login
user_session = httpx.Client(headers={
    "User-Agent": "Mozilla/5.0 (Linux; Android 12; M2007J20CG Build/SKQ1.211019.001) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/135.0.7049.38 Mobile Safari/537.36"
}, follow_redirects=False)

cookies = None

# ----------- HANDLE /login ------------
async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Kirim email dan password blacktowhite kamu dalam format:\n\n email|password")

# ----------- HANDLE CREDENTIAL ------------
async def handle_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cookies
    if "|" not in update.message.text:
        return await update.message.reply_text("Format salah. Gunakan email|password")

    email, password = update.message.text.strip().split("|")

    try:
        # Step 1: GET login page
        resp = user_session.get("https://www.blacktowhite.net/login/login")
        soup = BeautifulSoup(resp.text, "html.parser")

        # Ambil CSRF token
        token = soup.find("input", {"name": "_xfToken"}).get("value")
        
        # Set cookie age_verified
        user_session.cookies.set("age_verified", "1")

        # Step 2: Kirim form login
        payload = {
            "_xfToken": token,
            "login": email,
            "password": password,
            "remember": "1",
            "_xfRedirect": "https://www.blacktowhite.net/"
        }

        headers = {
            "Referer": "https://www.blacktowhite.net/login/login",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": user_session.headers["User-Agent"]
        }

        login_post = user_session.post("https://www.blacktowhite.net/login/login", data=payload, headers=headers)

        # Step 3: Cek apakah login berhasil
        if login_post.status_code == 303 and 'xf_user' in user_session.cookies:
            cookies = user_session.cookies
            await update.message.reply_text("Login sukses! Kirim link halaman medianya.")
        else:
            await update.message.reply_text("Login gagal. Coba cek email/password.")
    except Exception as e:
        await update.message.reply_text(f"Gagal login: {e}")

# ----------- HANDLE LINK PAGE MEDIANYA ------------
async def handle_media_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if cookies is None:
        return await update.message.reply_text("Kamu belum login! Ketik /login untuk login dulu.")

    # Ambil link page media dari user
    media_page_url = update.message.text.strip()

    # Step 1: Scrape page media
    try:
        response = user_session.get(media_page_url, cookies=cookies)
        if response.status_code != 200:
            return await update.message.reply_text("Gagal mengambil halaman. Cek URL dan coba lagi.")

        # Parse halaman dengan BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        video_links = [video.get("href") for video in soup.find_all("a", href=True) if "video" in video["href"]]

        if not video_links:
            return await update.message.reply_text("Tidak ada video yang ditemukan di halaman ini.")

        # Kirim jumlah video yang ditemukan
        await update.message.reply_text(f"Jumlah video yang ditemukan: {len(video_links)}\nKlik 'Lanjut' untuk mulai mengunduh.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Lanjut", callback_data="download_videos")]
        ]))

        # Simpan video links di context
        context.user_data["video_links"] = video_links

    except Exception as e:
        await update.message.reply_text(f"Terjadi kesalahan: {e}")

# ----------- HANDLE DOWNLOAD VIDEO ------------
async def download_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video_links = context.user_data.get("video_links", [])
    if not video_links:
        return await update.message.reply_text("Tidak ada video untuk diunduh. Kirim link page media terlebih dahulu.")

    # Mulai download video
    try:
        for video_url in video_links:
            await update.message.reply_text(f"Men-download video: {video_url}")
            video_data = user_session.get(video_url)
            
            # Kirim video ke user
            await update.message.reply_video(video_data.content)
        
        await update.message.reply_text("Semua video telah diunduh.")

    except Exception as e:
        await update.message.reply_text(f"Terjadi kesalahan saat mengunduh video: {e}")

# ----------- MAIN FUNCTION ------------
def main():
    # Buat aplikasi Telegram bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Daftarkan handler
    app.add_handler(CommandHandler("login", login_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_credentials))  # Handle email|password
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_media_link))  # Handle link page
    app.add_handler(CallbackQueryHandler(download_videos, pattern="download_videos"))

    # Jalankan bot
    app.run_polling()

if __name__ == "__main__":
    main()