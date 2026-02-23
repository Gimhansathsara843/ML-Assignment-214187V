import requests
import json
import time
import pandas as pd
from bs4 import BeautifulSoup
import re
import os
import csv

class BaseScraper:
    def __init__(self, base_url, delay=1.5, retries=3):
        self.base_url = base_url
        self.delay = delay
        self.retries = retries
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def get_page(self, url):
        for i in range(self.retries):
            try:
                time.sleep(self.delay)
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    return response
                print(f"Status {response.status_code} for {url}. Retrying...")
            except Exception as e:
                print(f"Error fetching {url} (Attempt {i+1}/{self.retries}): {e}")
        return None

def save_to_csv(item, filename="sri_lanka_mobile_phone_listings.csv"):
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=item.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(item)

class FranciumScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://francium.lk")

    def scrape(self):
        print("Scraping Francium...")
        page = 1
        count = 0
        while True:
            url = f"{self.base_url}/products.json?limit=250&page={page}"
            response = self.get_page(url)
            if not response: break
            
            data = response.json()
            products = data.get("products", [])
            if not products: break
            
            for prod in products:
                title = prod.get("title", "").lower()
                p_type = prod.get("product_type", "").lower()
                tags = [t.lower() for t in prod.get("tags", [])]
                
                if any(kw in title or kw in p_type or kw in tags for kw in ["iphone", "samsung", "pixel", "xiaomi", "redmi", "phone", "mobile"]):
                    variants = prod.get("variants", [])
                    price = variants[0].get("price") if variants else None
                    
                    item = {
                        "Product title": prod.get("title"),
                        "Brand": prod.get("vendor"),
                        "Model": prod.get("title"),
                        "Total price (LKR)": price,
                        "Discount price (if available)": None,
                        "RAM": self.extract_spec(prod.get("body_html"), "RAM"),
                        "Storage": self.extract_spec(prod.get("title") + " " + prod.get("body_html"), "Storage"),
                        "Processor": None,
                        "Battery capacity": None,
                        "Camera specs": None,
                        "Display size": None,
                        "Operating system": "iOS" if "iphone" in title else "Android",
                        "Network type": None,
                        "Warranty": "Yes" if "warranty" in prod.get("body_html", "").lower() else "unknown",
                        "Stock availability": "In stock" if any(v.get("available") for v in variants) else "Out of stock",
                        "Seller / store name": "Francium",
                        "Posted date": prod.get("published_at"),
                        "Product URL": f"{self.base_url}/products/{prod.get('handle')}"
                    }
                    save_to_csv(item)
                    count += 1
            page += 1
            if page > 5: break
        print(f"Francium: Saved {count} listings.")

    def extract_spec(self, text, spec_type):
        if not text: return None
        if spec_type == "Storage":
            match = re.search(r'(\d+)\s*(GB|TB)', text, re.IGNORECASE)
            return match.group(0) if match else None
        return None

class IkmanScraper(BaseScraper):
    def __init__(self):
        super().__init__("https://ikman.lk")

    def scrape(self, start_page=1, end_page=300):
        print(f"Scraping Ikman pages {start_page} to {end_page}...")
        total_saved = 0
        for page in range(start_page, end_page + 1):
            url = f"{self.base_url}/en/ads/sri-lanka/mobile-phones?page={page}"
            response = self.get_page(url)
            if not response: continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            listings = soup.find_all(['li', 'div'], class_=re.compile(r'ad|item|listing'))
            
            page_items = 0
            for ad in listings:
                item = self.parse_ad(ad)
                if item and item["Product title"]:
                    save_to_csv(item)
                    page_items += 1
                    total_saved += 1
            
            # Fallback if specific classes missed
            if page_items == 0:
                h2s = soup.find_all('h2')
                for h2 in h2s:
                    ad = h2.find_parent(['li', 'div'])
                    if ad:
                        item = self.parse_ad(ad)
                        if item:
                            save_to_csv(item)
                            page_items += 1
                            total_saved += 1
            
            print(f"Page {page}: Saved {page_items} items (Total Ikman: {total_saved})")
            if page_items == 0 and page > start_page + 5: break
            if total_saved > 8000: break
        return total_saved

    def parse_ad(self, ad):
        try:
            title_elem = ad.find(['h2', 'span'], class_=re.compile(r'title|heading'))
            if not title_elem: return None
            title = title_elem.get_text(strip=True)
            if not title: return None
            
            price_elem = ad.find(['div', 'span'], class_=re.compile(r'price|amount'))
            price = price_elem.get_text(strip=True) if price_elem else None
            
            link_elem = ad.find('a')
            href = link_elem.get('href') if link_elem else None
            url = self.base_url + href if href and href.startswith('/') else href or "unknown"
            
            brand = "unknown"
            for b in ["Apple", "Samsung", "Xiaomi", "Vivo", "Oppo", "Huawei", "Realme", "Nokia", "Google", "Sony", "OnePlus", "Honor", "Infinix"]:
                if b.lower() in title.lower():
                    brand = b
                    break
            
            return {
                "Product title": title,
                "Brand": brand,
                "Model": title,
                "Total price (LKR)": price,
                "Discount price (if available)": None,
                "RAM": self.extract_spec(title, "RAM"),
                "Storage": self.extract_spec(title, "Storage"),
                "Processor": None,
                "Battery capacity": None,
                "Camera specs": None,
                "Display size": None,
                "Operating system": "iOS" if "iphone" in title.lower() else "Android",
                "Network type": None,
                "Warranty": "unknown",
                "Stock availability": "In stock",
                "Seller / store name": "Ikman Seller",
                "Posted date": "Recently",
                "Product URL": url
            }
        except: return None

    def extract_spec(self, text, spec_type):
        if spec_type == "Storage":
            match = re.search(r'(\d+)\s*(GB|TB)', text, re.IGNORECASE)
            return match.group(0) if match else None
        elif spec_type == "RAM":
            match = re.search(r'(\d+)\s*GB\s*RAM', text, re.IGNORECASE)
            return match.group(0) if match else None
        return None

if __name__ == "__main__":
    csv_file = "sri_lanka_mobile_phone_listings.csv"
    # Note: NOT removing file this time, to append. 
    # Actually my save_to_csv already appends.
    
    i_scraper = IkmanScraper()
    # Start from where we left off
    i_scraper.scrape(start_page=237, end_page=350)
    
    print("Scraping complete. Cleaning and deduplicating...")
    df = pd.read_csv(csv_file)
    
    def clean_price(val):
        if not val or pd.isna(val): return None
        nums = re.findall(r'\d+', str(val).split('.')[0].replace(',', ''))
        return "".join(nums) if nums else None

    df['Total price (LKR)'] = df['Total price (LKR)'].apply(clean_price)
    # Deduplicate by URL to ensure uniqueness
    df = df.drop_duplicates(subset=["Product URL"])
    # Also deduplicate by title/price as a fall back
    df = df.drop_duplicates(subset=["Product title", "Total price (LKR)"])
    df.to_csv(csv_file, index=False, encoding="utf-8")
    print(f"Final dataset size: {len(df)} unique listings.")
