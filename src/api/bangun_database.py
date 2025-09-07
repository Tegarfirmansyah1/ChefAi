# bangun_database.py

import os
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

# 1. Tentukan path ke folder berisi resep dan folder untuk database
RESEP_PATH = "resep"
DB_PATH = "db_resep"

print("Memulai proses pembangunan database resep...")

# 2. Muat (Load) semua dokumen dari folder 'resep'
# DirectoryLoader akan otomatis mencari semua file .txt di folder tersebut
print(f"Memuat dokumen dari folder: {RESEP_PATH}")
loader = DirectoryLoader(RESEP_PATH, glob="*.txt", loader_cls=TextLoader, loader_kwargs={'autodetect_encoding': True})
documents = loader.load()
if not documents:
    print(f"Tidak ada dokumen .txt yang ditemukan di folder '{RESEP_PATH}'. Pastikan file resep sudah ada.")
    exit()
print(f"Berhasil memuat {len(documents)} dokumen.")


# 3. Potong (Split) dokumen menjadi bagian-bagian kecil (chunks)
# Ini penting agar model bisa fokus pada bagian resep yang paling relevan.
print("Memotong dokumen menjadi chunks...")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=400)
chunks = text_splitter.split_documents(documents)
print(f"Total chunks yang dibuat: {len(chunks)}")


# 4. Buat model Embedding
# Model ini yang akan mengubah teks chunks menjadi vektor (angka).
print("Menyiapkan model embedding (membutuhkan koneksi internet saat pertama kali)...")
embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
print("Model embedding siap.")


# 5. Masukkan chunks ke dalam ChromaDB dan simpan secara lokal
# Proses ini akan membuat folder 'db_resep' dan menyimpan semua vektor di dalamnya.
print(f"Membuat dan menyimpan vector database di: {DB_PATH}")
db = Chroma.from_documents(
    chunks, 
    embedding_function, 
    persist_directory=DB_PATH
)
print("✅ Database resep berhasil dibuat dan disimpan!")