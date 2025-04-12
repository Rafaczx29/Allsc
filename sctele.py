import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor

# Ganti dengan token Telegram bot kamu
API_TOKEN = '7538833331:AAG9JvhSWm5r5SZKnXRMgL8F92MINNardCc'
YOUR_ADMIN_USER_ID = 1271362249  # Ganti dengan ID kamu sebagai admin

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Koneksi ke database SQLite
conn = sqlite3.connect('store_db.sqlite')
cursor = conn.cursor()

# Buat tabel jika belum ada
cursor.execute('''CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, description TEXT, price REAL, stock INTEGER, file_url TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, user_id INTEGER, product_id INTEGER, status TEXT, screenshot_url TEXT)''')
conn.commit()

# Perintah /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Selamat datang di Toko Digital! Pilih produk yang kamu inginkan.")
    
    # Ambil produk dari database
    cursor.execute("SELECT * FROM products WHERE stock > 0")
    products = cursor.fetchall()
    
    if products:
        for product in products:
            await message.answer(f"{product[1]} - {product[3]} IDR\nDeskripsi: {product[2]}\nStok: {product[4]}\nKlik untuk beli!")
    else:
        await message.answer("Saat ini tidak ada produk yang tersedia.")

# Handler ketika user memilih produk
@dp.message_handler(lambda message: message.text.startswith("Beli"))
async def buy_product(message: types.Message):
    product_id = int(message.text.split()[-1])  # Mengambil ID produk dari tombol
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    
    if product and product[4] > 0:  # Jika produk ada dan stok > 0
        cursor.execute("INSERT INTO orders (user_id, product_id, status) VALUES (?, ?, ?)", (message.from_user.id, product_id, 'Menunggu Pembayaran'))
        conn.commit()
        await message.answer(f"Terima kasih! Produk {product[1]} kamu sedang diproses. Silakan kirim screenshot bukti pembayaran via QRIS.")
    else:
        await message.answer("Maaf, produk ini sudah habis atau tidak tersedia.")

# Handler untuk menerima screenshot
@dp.message_handler(content_types=['photo'])
async def handle_screenshot(message: types.Message):
    # Simpan URL foto yang dikirim
    screenshot_url = message.photo[-1].file_id
    cursor.execute("UPDATE orders SET screenshot_url = ?, status = ? WHERE user_id = ? AND status = 'Menunggu Pembayaran'", (screenshot_url, 'Pembayaran Diterima', message.from_user.id))
    conn.commit()
    await message.answer("Terima kasih atas bukti pembayaranmu! Order kamu sedang diproses.")

# Admin panel
@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    if message.from_user.id == YOUR_ADMIN_USER_ID:  # Cek apakah yang chat adalah admin
        await message.answer("Selamat datang di panel admin. Pilih perintah yang ingin dijalankan:\n- /add_product\n- /remove_product\n- /list_products")
    else:
        await message.answer("Kamu bukan admin!")

# Perintah untuk menambahkan produk
@dp.message_handler(commands=['add_product'])
async def add_product(message: types.Message):
    if message.from_user.id == YOUR_ADMIN_USER_ID:
        await message.answer("Kirimkan nama produk terlebih dahulu.")
        await bot.register_next_step_handler(message, process_product_name)
    else:
        await message.answer("Kamu bukan admin!")

async def process_product_name(message: types.Message):
    product_name = message.text
    await message.answer("Sekarang, kirimkan deskripsi produk.")
    await bot.register_next_step_handler(message, process_product_description, product_name)

async def process_product_description(message: types.Message, product_name: str):
    product_description = message.text
    await message.answer("Sekarang, kirimkan harga produk (angka saja).")
    await bot.register_next_step_handler(message, process_product_price, product_name, product_description)

async def process_product_price(message: types.Message, product_name: str, product_description: str):
    try:
        product_price = float(message.text)
        await message.answer("Sekarang, kirimkan stok produk yang tersedia (angka saja).")
        await bot.register_next_step_handler(message, process_product_stock, product_name, product_description, product_price)
    except ValueError:
        await message.answer("Harga produk tidak valid, harap kirimkan angka saja.")

async def process_product_stock(message: types.Message, product_name: str, product_description: str, product_price: float):
    try:
        product_stock = int(message.text)
        await message.answer("Terakhir, kirimkan link atau file produk digital (bisa berupa URL atau file).")
        await bot.register_next_step_handler(message, process_product_file_url, product_name, product_description, product_price, product_stock)
    except ValueError:
        await message.answer("Stok produk tidak valid, harap kirimkan angka saja.")

async def process_product_file_url(message: types.Message, product_name: str, product_description: str, product_price: float, product_stock: int):
    product_file_url = message.text
    cursor.execute("INSERT INTO products (name, description, price, stock, file_url) VALUES (?, ?, ?, ?, ?)", (product_name, product_description, product_price, product_stock, product_file_url))
    conn.commit()
    await message.answer(f"Produk {product_name} telah berhasil ditambahkan!")

# Perintah untuk menghapus produk
@dp.message_handler(commands=['remove_product'])
async def remove_product(message: types.Message):
    if message.from_user.id == YOUR_ADMIN_USER_ID:
        await message.answer("Kirimkan ID produk yang ingin dihapus.")
        await bot.register_next_step_handler(message, process_remove_product)
    else:
        await message.answer("Kamu bukan admin!")

async def process_remove_product(message: types.Message):
    try:
        product_id = int(message.text)
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        await message.answer(f"Produk dengan ID {product_id} telah berhasil dihapus!")
    except ValueError:
        await message.answer("ID produk tidak valid, harap kirimkan ID produk yang benar.")

# Perintah untuk melihat daftar produk
@dp.message_handler(commands=['list_products'])
async def list_products(message: types.Message):
    if message.from_user.id == YOUR_ADMIN_USER_ID:
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        if products:
            for product in products:
                await message.answer(f"ID: {product[0]}\nNama: {product[1]}\nDeskripsi: {product[2]}\nHarga: {product[3]} IDR\nStok: {product[4]}\nURL: {product[5]}\n")
        else:
            await message.answer("Tidak ada produk di toko saat ini.")
    else:
        await message.answer("Kamu bukan admin!")

if __name__ == '__main__':
    executor.start_polling(dp)