import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import os
import re
import traceback

def scrape_resep_selenium(url):
    webdriver_path = 'chromedriver-win64/chromedriver.exe'
    service = Service(executable_path=webdriver_path)
    options = webdriver.ChromeOptions()
    options.add_argument('--log-level=3')
    driver = webdriver.Chrome(service=service, options=options)

    try:
        print(f"Membuka URL dengan Selenium: {url}")
        driver.get(url)
        time.sleep(5) 

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # --- BAGIAN EKSTRAKSI DATA YANG BARU DAN LEBIH CANGGIH ---

        title_element = soup.find('h1')
        title = title_element.text.strip() if title_element else "Tanpa Judul"
        print(f"Menemukan resep: {title}")

        # --- Ekstrak Bahan-Bahan (Logika Baru) ---
        ingredients_container = soup.find('div', class_=lambda c: c and '_recipe-ingredients' in c)
        ingredients_list = []
        if ingredients_container:
            # Cari semua judul grup (Bahan, Bumbu kering, Bumbu halus)
            groups = ingredients_container.find_all('p', class_='recipe-ingredients-title')
            for group in groups:
                group_title = group.text.strip()
                if group_title: # Tambahkan judul grup jika ada isinya
                    ingredients_list.append(f"\n{group_title}:")
                
                # Cari semua item bahan setelah judul grup ini dan sebelum judul grup berikutnya
                # find_next_siblings() adalah trik canggih BeautifulSoup
                for item_container in group.find_next_siblings('div', class_='d-flex'):
                    part_div = item_container.find('div', class_='part')
                    item_div = item_container.find('div', class_='item')
                    
                    if part_div and item_div:
                        quantity = part_div.text.strip()
                        # Gabungkan semua teks di dalam item_div untuk mendapatkan nama bahan
                        item_name = ' '.join(item_div.text.split())
                        ingredients_list.append(f"- {quantity} {item_name}")

        # --- Ekstrak Langkah-langkah (Logika Baru) ---
        steps_container = soup.find('div', class_=lambda c: c and '_recipe-steps' in c)
        steps_list = []
        if steps_container:
            # Cari semua div yang mewakili satu langkah
            for step_div in steps_container.find_all('div', class_='step'):
                step_content = step_div.find('div', class_='content')
                if step_content:
                    # Ambil teks dari paragraf di dalamnya
                    steps_list.append(step_content.p.text.strip())

        if not ingredients_list or not steps_list:
            print("Gagal menemukan bahan atau langkah-langkah dengan struktur baru.")
            return

        # --- Sisa kode untuk formatting dan saving SAMA PERSIS ---
        formatted_text = f"Judul: {title}\n"
        
        # Tambahkan bahan-bahan yang sudah dikelompokkan
        for ingredient in ingredients_list:
            # Cek jika item adalah judul grup
            if ":" in ingredient:
                formatted_text += f"{ingredient}\n"
            else:
                formatted_text += f"  {ingredient}\n"

        formatted_text += "\nLangkah-langkah:\n"
        for i, step in enumerate(steps_list, 1):
            formatted_text += f"{i}. {step}\n"

        if not os.path.exists('resep'):
            os.makedirs('resep')

        safe_filename = re.sub(r'[\\/*?:"<>|]', "", title)
        safe_filename = safe_filename.replace(" ", "_") + ".txt"
        
        filepath = os.path.join('resep', safe_filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(formatted_text)

        print(f"✅ Resep berhasil disimpan di: {filepath}")

    except Exception as e:
        print(f"Terjadi error: {e}")
        traceback.print_exc() 
    finally:
        driver.quit()

