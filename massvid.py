import os
import subprocess
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler, ContextTypes

# Ganti dengan token bot kamu
BOT_TOKEN = "7956681803:AAFwnc47NYn7-83jQUFr42GJajZp_JYFoKM"
# Ganti dengan data login
USER_EMAIL = None
USER_PASSWORD = None

# Fungsi login untuk mengambil cookies
def login_to_blacktowhite(email, password):
    login_url = 'https://www.blacktowhite.net/login/login'
    session = requests.Session()
    login_data = {
        'email': email,
        'password': password,
        'remember_me': 'on'
    }
    response = session.post(login_url, data=login_data)
    if response.url == "https://www.blacktowhite.net/":
        return session
    return None

# Fungsi untuk scraping video dari halaman media
def scrape_videos(page_url, session):
    response = session.get(page_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Mengambil link video dari halaman
    video_links = []
    for video in soup.find_all('a', class_='video-thumbnail'):
        video_url = video.get('href')
        if video_url:
            video_links.append('https://www.blacktowhite.net' + video_url)

    return video_links

# Handler untuk login
async def start_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Masukkan email dan password untuk login (format: email|password).")

# Handler untuk menerima email dan password
async def handle_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global USER_EMAIL, USER_PASSWORD
    user_input = update.message.text.strip()
    
    if "|" not in user_input:
        await update.message.reply_text("Format salah. Harap masukkan email dan password dengan format email|password.")
        return
    
    USER_EMAIL, USER_PASSWORD = user_input.split('|')
    session = login_to_blacktowhite(USER_EMAIL, USER_PASSWORD)
    
    if session:
        await update.message.reply_text("Login sukses! Kirim link halaman media yang ingin di-scrape.")
        context.user_data['session'] = session  # Simpan session untuk keperluan selanjutnya
    else:
        await update.message.reply_text("Login gagal. Cek email dan password kamu.")

# Handler untuk menerima link dan mengscrape video
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'session' not in context.user_data:
        await update.message.reply_text("Kamu perlu login terlebih dahulu. Ketik /login untuk memulai.")
        return
    
    session = context.user_data['session']
    url = update.message.text.strip()
    
    await update.message.reply_text("Sedang mengscrape halaman... Tunggu sebentar.")
    
    video_links = scrape_videos(url, session)
    
    if not video_links:
        await update.message.reply_text("Tidak ada video ditemukan di halaman ini.")
        return
    
    # Mengirim jumlah video dan tombol untuk melanjutkan
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Lanjut", callback_data="download_videos")]])
    await update.message.reply_text(f"Total video ditemukan: {len(video_links)}", reply_markup=reply_markup)
    
    context.user_data['video_links'] = video_links  # Simpan video links

# Handler untuk mendownload video
async def download_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'video_links' not in context.user_data:
        await update.message.reply_text("Tidak ada video yang tersedia untuk di-download.")
        return
    
    video_links = context.user_data['video_links']
    chat_id = update.message.chat_id
    
    # Kirim video satu per satu
    for video_link in video_links:
        # Ambil nama video dengan cara sederhana
        video_name = video_link.split('/')[-1] + '.mp4'
        
        await update.message.reply_text(f"Sedang mengirim video: {video_name}")
        
        # Download video menggunakan yt-dlp
        subprocess.run(['yt-dlp', '-o', video_name, video_link])
        
        with open(video_name, 'rb') as vid:
            await context.bot.send_video(chat_id=chat_id, video=vid)
        
        # Hapus file setelah mengirim
        os.remove(video_name)

# Setup bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Tambahkan handler
    app.add_handler(CommandHandler("login", start_login))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_login))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_handler(InlineQueryHandler(download_videos, pattern="download_videos"))
    
    print("Bot aktif, kirim perintah 'LOGIN' untuk memulai.")
    app.run_polling()

if __name__ == "__main__":
    main()