import os
import re
import aiohttp
import subprocess
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = "TOKEN_BOT_LOE_DISINI"

user_video_links = {}

async def scrape_video_links(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/media/" in href and ("videos/" in href or href.endswith(".mp4")):
                    if not href.startswith("http"):
                        href = "https://blacktowhite.net" + href
                    links.append(href)
            return list(set(links))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.message.chat_id

    if not url.startswith("http"):
        await update.message.reply_text("Kirim link halaman yang valid, bro.")
        return

    await update.message.reply_text("Sedang cari video di halaman itu bro...")

    links = await scrape_video_links(url)

    if not links:
        await update.message.reply_text("Gak ketemu video bro di halaman itu.")
        return

    user_video_links[chat_id] = links

    await update.message.reply_text(
        f"Ditemukan {len(links)} video.\nKirim semua sekarang?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Lanjut Kirim", callback_data="send_videos")]
        ])
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    if query.data == "send_videos":
        links = user_video_links.get(chat_id, [])
        if not links:
            await query.edit_message_text("Gagal ambil link video bro.")
            return

        await query.edit_message_text("Mulai kirim video...")

        files_before = set(os.listdir())
        for i, link in enumerate(links):
            await context.bot.send_message(chat_id, f"Download video {i+1}...\n{link}")
            subprocess.run(["yt-dlp", "-f", "best", "-o", "%(title)s.%(ext)s", link],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        files_after = set(os.listdir())
        new_files = sorted(list(files_after - files_before), key=os.path.getctime)
        video_files = [f for f in new_files if f.lower().endswith((".mp4", ".mkv", ".mov"))]

        for vid_file in video_files:
            try:
                with open(vid_file, 'rb') as vid:
                    await context.bot.send_video(chat_id=chat_id, video=vid)
            except Exception as e:
                await context.bot.send_message(chat_id, f"Gagal kirim {vid_file}: {e}")
            os.remove(vid_file)

        await context.bot.send_message(chat_id, "Selesai kirim semua videonya bro.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    print("Bot aktif bro! Kirim link page blacktowhite, nanti bot scrape & siapin kirim video.")
    app.run_polling()