from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.parse
import time

BASE_URL = "https://ananas.mk"
CATEGORY_URL = f"{BASE_URL}/kategorii/telefoni-foto/mobilni-telefoni/pametni-telefoni"

BRANDS = ["Samsung", "Apple", "Xiaomi", "Honor"]

# words to remove from phone name
NAME_PREFIXES = [
    "мобилен телефон",
    "паметен телефон",
    "mobile phone",
    "smartphone"
]


class Phone:
    def __init__(self, name, brand, price, image_url, url):
        self.name      = name
        self.brand     = brand
        self.price     = price
        self.image_url = image_url
        self.url       = url

    def __repr__(self):
        return (f"Phone(name={self.name}, brand={self.brand}, "
                f"price={self.price}, image_url={self.image_url}, url={self.url})")


def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    return driver


def wait_for_cards(driver, timeout=15):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/proizvod/']"))
        )
        time.sleep(2)
        return True
    except:
        return False


def detect_brand(name):
    # detect on original name before lowercasing
    name_lower = name.lower()
    for brand in BRANDS:
        if brand.lower() in name_lower:
            return brand.lower()
    return None


def clean_name(name):
    name = name.lower().strip()
    for prefix in NAME_PREFIXES:
        name = name.replace(prefix, "").strip()
    return name


def get_real_image(img, driver):
    src = img.get_attribute("src") or ""
    # if placeholder, wait briefly and re-read after scroll
    if src.startswith("data:"):
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img)
        time.sleep(0.5)
        src = img.get_attribute("src") or ""
    # unwrap next.js image proxy /_next/image?url=...
    if "/_next/image?url=" in src:
        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(src).query)
        src = urllib.parse.unquote(parsed.get("url", [""])[0])
    return src if src and not src.startswith("data:") else "N/A"


def scrape_all_phones():
    driver = get_driver()
    phones = []
    seen_urls = set()
    page = 1

    while True:
        url = f"{CATEGORY_URL}?page={page}"
        print(f"Scraping page {page} -> {url}")
        driver.get(url)

        loaded = wait_for_cards(driver)
        if not loaded:
            print(f"No cards on page {page}, stopping.")
            break

        # scroll to bottom to trigger lazy loading of all cards
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        cards = driver.find_elements(By.CSS_SELECTOR, "a[href*='/proizvod/']")
        print(f"Found {len(cards)} products on page {page}")

        if not cards:
            break

        # duplicate page check
        page_urls = [c.get_attribute("href") for c in cards]
        new_urls = [u for u in page_urls if u not in seen_urls]
        if not new_urls:
            print(f"Page {page} is a duplicate, stopping.")
            break

        for card in cards:
            try:
                href = card.get_attribute("href") or "N/A"
                if href in seen_urls:
                    continue
                seen_urls.add(href)

                if href.startswith("/"):
                    href = BASE_URL + href

                # raw name for brand detection before cleaning
                try:
                    raw_name = card.find_element(By.CSS_SELECTOR, "h3").text.strip()
                except:
                    raw_name = "N/A"

                # detect brand from raw name, returns lowercase
                brand = detect_brand(raw_name)
                if brand is None:
                    continue

                # clean and lowercase name
                name = clean_name(raw_name)

                # price
                try:
                    price = "N/A"
                    price_spans = card.find_elements(By.CSS_SELECTOR, "span")
                    for span in reversed(price_spans):
                        clean = span.text.strip().replace(".", "").replace(",", "")
                        if clean.isdigit() and len(clean) >= 3:
                            price = span.text.strip()
                            break
                except:
                    price = "N/A"

                # image — pass driver so we can scrollIntoView for lazy loaded ones
                try:
                    img = card.find_element(By.CSS_SELECTOR, "img")
                    image_url = get_real_image(img, driver)
                except:
                    image_url = "N/A"

                phones.append(Phone(
                    name=name,
                    brand=brand,
                    price=price,
                    image_url=image_url,
                    url=href,
                ))
                print(f"  + [{brand}] {name}")

            except Exception as e:
                print(f"  Skipped a card: {e}")

        page += 1

    driver.quit()
    return phones


if __name__ == "__main__":
    print("Starting ananas.mk phone scraper...\n")
    phones = scrape_all_phones()
    print(f"\n{'='*50}")
    print(f"Total phones scraped: {len(phones)}")
    print(f"{'='*50}")
    for brand in BRANDS:
        count = len([p for p in phones if p.brand == brand.lower()])
        print(f"  {brand}: {count} phones")
    print()
    for phone in phones:
        print(phone)