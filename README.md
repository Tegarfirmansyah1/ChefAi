# Chef Chimi - Asisten Resep AI 

Chef Chimi adalah aplikasi web full-stack canggih yang berfungsi sebagai asisten resep masakan Indonesia. Dibangun dengan arsitektur RAG (Retrieval-Augmented Generation), aplikasi ini mampu memberikan jawaban yang akurat berdasarkan database resep yang dinamis, serta dapat berinteraksi dengan pengguna secara kontekstual layaknya asisten sungguhan. Proyek ini dirancang untuk di-deploy sebagai satu kesatuan di Vercel.

# Fitur Utama
- Percakapan Kontekstual: Dilengkapi dengan memori, Chef Chimi mampu memahami pertanyaan lanjutan dan menjaga alur percakapan.

- Arsitektur RAG Canggih: Jawaban dihasilkan berdasarkan database resep yang relevan, meminimalkan halusinasi dan memastikan akurasi.

- Persona & Keamanan Terkunci: Menggunakan arsitektur "Penjaga Gerbang" (Gatekeeper) untuk mendeteksi niat pengguna, menolak permintaan di luar topik, dan menjaga persona AI sebagai koki.

- Database Dinamis: Database resep dibangun menggunakan web scraper (Selenium & BeautifulSoup) yang dapat diperbarui secara otomatis.

- Antarmuka Modern: UI chat yang responsif dan interaktif dibangun dengan Next.js dan Tailwind CSS, dengan fitur streaming untuk respons AI.

- Fleksibilitas Model: Dirancang untuk dapat beralih antara model AI lokal (untuk pengembangan) dan model berbasis API (Google Gemini) untuk produksi.

# Teknologi yang Digunakan
## Frontend
- Framework: Next.js (React)

- Bahasa: TypeScript

- Styling: Tailwind CSS

## Backend
- Runtime: Vercel Serverless Functions

- Bahasa: Python

- Orkestrasi AI: LangChain

- Model LLM: Gemma (Lokal) / Google Gemini API (Produksi)

- Vector Database: ChromaDB

- Web Scraping: Selenium, BeautifulSoup4


# Cara Menjalankan Proyek (Lokal)
Prerequisites
Python 3.9+

Node.js & npm

Vercel CLI: npm install -g vercel

(Opsional) LM Studio atau Ollama untuk menjalankan model lokal.

1. Setup Awal
Klona Repository

git clone <https://github.com/Tegarfirmansyah1/ChefAi>

Install Dependensi Frontend

npm install

Install Dependensi Backend

Pastikan Anda sudah membuat dan mengaktifkan virtual environment
pip install -r src/api/requirements.txt

Atur Environment Variable
Buat file .env.local di folder utama dan isi dengan GOOGLE_API_KEY Anda.

GOOGLE_API_KEY="AIz..."

Bangun Database Resep
Pastikan folder src/api/resep sudah berisi file-file .txt resep, lalu jalankan:

python src/api/bangun_database.py

2. Menjalankan Server Development
Vercel CLI memungkinkan kita menjalankan frontend dan backend secara bersamaan.

Jalankan dari folder utama proyek
vercel dev
