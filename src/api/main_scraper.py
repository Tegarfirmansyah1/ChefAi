import time
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Impor fungsi scraper yang sudah kita buat sebelumnya
from scraper import scrape_resep_selenium

def get_recipe_links(category_url):
    """
    Fungsi untuk mengunjungi SATU halaman kategori dan mengumpulkan semua link resep.
    (Fungsi ini tidak perlu diubah)
    """
    webdriver_path = 'chromedriver-win64/chromedriver.exe'
    service = Service(executable_path=webdriver_path)
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    options.add_argument('--log-level=3')
    driver = webdriver.Chrome(service=service, options=options)
    
    print(f"Mengambil daftar link resep dari: {category_url}")
    
    try:
        driver.get(category_url)
        print("Menunggu halaman kategori dimuat...")
        time.sleep(5) 

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        links = []
        recipe_containers = soup.find_all('div', class_='_recipe-card')
        
        for container in recipe_containers:
            link_tag = container.find('a', class_='stretched-link', href=True)
            if link_tag:
                absolute_link = urljoin(category_url, link_tag['href'])
                links.append(absolute_link)
                
        unique_links = list(set(links))
        print(f"Berhasil menemukan {len(unique_links)} link resep unik di halaman ini.")
        return unique_links
        
    except Exception as e:
        print(f"Gagal mengambil daftar link dari halaman {category_url}: {e}")
        return []
    finally:
        driver.quit()

def generate_safe_filename(title):
    """Fungsi helper untuk membuat nama file yang aman dari judul."""
    safe_filename = re.sub(r'[\\/*?:"<>|]', "", title)
    return safe_filename.replace(" ", "_") + ".txt"

# --- FUNGSI UTAMA YANG DIMODIFIKASI UNTUK FITUR RESUME ---
if __name__ == "__main__":
    BASE_URL = "https://www.masakapahariini.com/resep/"
    
    # Tentukan halaman awal dan akhir untuk scraping
    START_PAGE = 2  
    END_PAGE = 4   
    # -----------------------
    
    all_links_from_all_pages = []

    print(f"--- Memulai Proses Pengumpulan Link dari Halaman {START_PAGE} hingga {END_PAGE} ---")

    # Fase 1: Loop melalui rentang halaman yang ditentukan
    for page_num in range(START_PAGE, END_PAGE + 1):
        if page_num == 1:
            current_page_url = BASE_URL
        else:
            current_page_url = f"{BASE_URL}page/{page_num}/"
        
        print(f"\n--- Mengumpulkan dari Halaman {page_num} ---")
        links_from_this_page = get_recipe_links(current_page_url)
        all_links_from_all_pages.extend(links_from_this_page)
        
        print("--- Jeda 3 detik sebelum ke halaman berikutnya ---")
        time.sleep(3)

    unique_total_links = list(set(all_links_from_all_pages))
    print(f"\n\n--- Total Link Unik Terkumpul: {len(unique_total_links)} ---")

    # Fase 2: Loop melalui setiap link dan scrape HANYA JIKA BELUM ADA
    if unique_total_links:
        print("\n--- Memulai Proses Scraping untuk Setiap Resep ---")
        
        scraped_count = 0
        skipped_count = 0
        
        for i, link in enumerate(unique_total_links, 1):
            print(f"\n--- Memproses Link {i}/{len(unique_total_links)}: {link} ---")
            
            # --- LOGIKA CERDAS UNTUK MELEWATKAN RESEP ---
            # Kita coba tebak nama file dari URL untuk cek apakah sudah ada
            try:
                # Ambil bagian terakhir dari URL sebagai judul sementara
                potential_title = link.strip('/').split('/')[-1].replace('-', ' ')
                potential_filename = generate_safe_filename(potential_title.title())
                filepath = os.path.join('resep', potential_filename)

                # Jika file sudah ada, lewati (continue) ke link berikutnya
                if os.path.exists(filepath):
                    print(f"File '{potential_filename}' sudah ada. Melewatkan...")
                    skipped_count += 1
                    continue
            except Exception:
                # Jika gagal menebak nama file, lanjutkan saja ke proses scrape
                pass
            # ----------------------------------------------
            
            # Jika belum ada, jalankan proses scraping
            scrape_resep_selenium(link)
            scraped_count += 1
            
            print("--- Memberi jeda 5 detik sebelum resep berikutnya ---")
            time.sleep(5)
            
        print(f"\n✅ Proses scraping selesai!")
        print(f"Resep baru di-scrape: {scraped_count}")
        print(f"Resep yang dilewati: {skipped_count}")
    else:
        print("\nTidak ada resep baru yang bisa di-scrape. Program berhenti.")