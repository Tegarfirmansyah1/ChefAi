# Chef Chimi 
- Asisten Resep AI Chef Chimi adalah aplikasi web full-stack canggih yang berfungsi sebagai asisten resep masakan Indonesia. Dibangun dengan arsitektur RAG (Retrieval-Augmented Generation), aplikasi ini mampu memberikan jawaban yang akurat berdasarkan database resep yang dinamis, serta dapat berinteraksi dengan pengguna secara kontekstual layaknya asisten sungguhan. Proyek ini siap di-deploy sebagai satu kesatuan di Vercel.

## Fitur UtamaPercakapan Kontekstual: Dilengkapi dengan memori, Chef Chimi mampu memahami pertanyaan lanjutan dan menjaga alur percakapan.
## Arsitektur RAG Canggih: Jawaban dihasilkan berdasarkan database resep yang relevan, meminimalkan halusinasi dan memastikan akurasi.
## Persona & Keamanan Terkunci: Menggunakan arsitektur "Penjaga Gerbang" (Gatekeeper) untuk mendeteksi niat pengguna, menolak permintaan di luar topik, dan menjaga persona AI sebagai koki.
## Database Dinamis: Database resep dibangun menggunakan web scraper (Selenium & BeautifulSoup) yang dapat diperbarui secara otomatis.
## Antarmuka Modern: UI chat yang responsif dan interaktif dibangun dengan Next.js dan Tailwind CSS, dengan fitur streaming untuk respons AI.
## Fleksibilitas Model: Dirancang untuk dapat beralih antara model AI lokal (untuk pengembangan) dan model berbasis API (Google Gemini) untuk produksi.

# Teknologi yang Digunakan
## Frontend (Next.js):
Framework: Next.js (React)
Bahasa: TypeScript
Styling: Tailwind CSS

## Backend (Vercel Serverless Functions):
Bahasa: Python
Framework API: FastAPI
Orkestrasi AI: LangChainModel 
LLM: Gemma (Lokal) / Google Gemini API (Produksi)
Vector Database: ChromaDBWeb 
Scraping: Selenium, BeautifulSoup4

📁 Struktur Direktori (Vercel Monorepo)Proyek ini menggunakan struktur monorepo yang memungkinkan frontend Next.js dan backend Python di-deploy bersamaan di Vercel.ai-chef-vercel/
|
├── app/                  # Folder inti dari Next.js (frontend)
│   └── page.tsx
├── public/
├── api/                  # Folder khusus untuk backend Python
│   ├── index.py          # File FastAPI utama (entrypoint)
│   ├── bangun_database.py
│   ├── scraper.py
│   ├── main_scraper.py
│   ├── db_resep/           # Database vektor
│   ├── resep/              # Kumpulan resep dalam format .txt
│   └── requirements.txt    # Dependensi Python
├── .env.local            # File API key untuk development
├── .gitignore
├── package.json
└── vercel.json           # File konfigurasi untuk Vercel
🚀 Cara Menjalankan Proyek (Lokal)PrerequisitesPython 3.9+Node.js & npmVercel CLI: npm install -g vercel(Opsional) LM Studio/Ollama untuk menjalankan model lokal.1. Setup Awal# Klona repository dan masuk ke direktori
git clone <URL_REPO_ANDA>
cd ai-chef-vercel

# Install dependensi frontend
npm install

# Install dependensi backend (dari dalam folder utama)
pip install -r api/requirements.txt

# Buat file .env.local dan isi dengan GOOGLE_API_KEY
# GOOGLE_API_KEY="AIz..."

# Bangun database resep dari folder 'resep'
python api/bangun_database.py
2. Menjalankan Server DevelopmentVercel CLI memungkinkan kita menjalankan frontend dan backend secara bersamaan dengan satu perintah.# Dari folder utama proyek
vercel dev
