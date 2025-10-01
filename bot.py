import os
import uuid
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import yt_dlp

# Semaphore = untuk membatasi jumlah proses download yang berjalan bersamaan
semaphore = asyncio.Semaphore(3)

# Batas ukuran file maksimal (dalam MB), agar tidak terlalu besar untuk dikirim via Telegram
MAX_FILE_MB = 50

# Ambil TOKEN dari Environment Variable
# TOKEN ini nanti kamu set di Railway atau di terminal (export TOKEN=...)
TOKEN = os.getenv("TOKEN")

# Fungsi utama untuk handle pesan dari user
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ambil teks dari user (seharusnya link IG)
    url = update.message.text.strip()

    # Validasi apakah teks mengandung link Instagram
    if "instagram.com" not in url:
        await update.message.reply_text("❌ Tolong kirim link Instagram yang valid.")PP
        return

    # Gunakan semaphore agar tidak terlalu banyak download sekaligus
    async with semaphore:
        # Buat nama file sementara yang unik (pakai UUID)
        filename = f"temp_{uuid.uuid4()}.mp4"

        # Opsi untuk yt-dlp → simpan video dalam format mp4 max 720p
        ydl_opts = {
            'outtmpl': filename,
            'format': 'mp4[height<=720]'
        }

        try:
            # Download video dari Instagram
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Cek ukuran file setelah didownload
            size_mb = os.path.getsize(filename) / (1024 * 1024)
            if size_mb > MAX_FILE_MB:
                os.remove(filename)  # hapus file agar tidak menumpuk
                await update.message.reply_text("⚠️ File terlalu besar (>50MB).")
                return

            # Kirim video ke user
            with open(filename, "rb") as f:
                await update.message.reply_video(f)

            # Hapus file setelah dikirim (biar tidak menumpuk di server)
            os.remove(filename)

        except Exception as e:
            # Jika ada error → kirim pesan error ke user
            await update.message.reply_text(f"Gagal download ❌: {str(e)}")

# Fungsi main → untuk menjalankan bot
def main():
    # Buat aplikasi Telegram dengan TOKEN
    app = Application.builder().token(TOKEN).build()

    # Tambahkan handler → kalau user kirim teks (bukan command), jalankan handle_message
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot sedang berjalan...")
    
    # Jalankan bot dengan polling (cek update dari Telegram secara rutin)
    app.run_polling()

# Jalankan main() kalau script ini dieksekusi langsung
if __name__ == "__main__":
    main()