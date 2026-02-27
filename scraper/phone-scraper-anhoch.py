from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


BASE_URL = "https://www.anhoch.com"
IMAGE_BASE_URL = "https://www.anhoch.com/storage/media/"
CATEGORY_URL = f"{BASE_URL}/categories/mobilni-telefoni/products?brand=&attribute=&toPrice=349980&inStockOnly=2&sort=latest&perPage=30&page="

# brands we want — detected from the product name
BRANDS = ["Samsung", "Apple", "Xiaomi", "Honor"]


class Phone:
    def __init__(self, name, brand, price, image_url, url):
        self.name      = name
        self.brand     = brand
        self.price     = price
        self.image_url = image_url
        self.url       = url

    def __repr__(self):
        return (f"Phone(name={self.name}, brand={self.brand}, "
                f"price={self.price}, image_url={self.image_url}, "
                f"url={self.url})")


def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
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
            EC.presence_of_element_located((By.CSS_SELECTOR, ".product-card")) # .product-card .col
        )
        time.sleep(1)
        return True
    except:
        return False


def detect_brand(name):
    name_lower = name.lower()
    for brand in BRANDS:
        if brand.lower() in name_lower:
            return brand
    return None


def scrape_all_phones():
    driver = get_driver()
    phones = []
    seen_urls = set()
    page = 1

    while True:
        #url = f"{CATEGORY_URL}?page={page}"

        url = f"{CATEGORY_URL}{page}"
        print(f"Scraping page {page} -> {url}")
        driver.get(url)
        #time.sleep(3)

        loaded = wait_for_cards(driver)
        if not loaded:
            print(f"No cards on page {page}, stopping.")
            break

        cards = driver.find_elements(By.CSS_SELECTOR, ".product-card") # .product-card .col

        if not cards:
            print(f"Empty page {page}, stopping.")
            break

        page_urls = []
        for card in cards:
            try:
                href = card.find_element(By.CSS_SELECTOR, "a.product-image").get_attribute("href")
                page_urls.append(href)
            except:
                page_urls.append("")

        new_urls = [u for u in page_urls if u not in seen_urls]
        if not new_urls:
            print(f"Page {page} is a duplicate, stopping.")
            break

        print(f"Found {len(cards)} products on page {page}, filtering by brand...")

        for card in cards:
            try:
                # name
                #name = card.find_element(By.CSS_SELECTOR, "a.product-name").text.strip() # bez h6 ?!??
                name_element = card.find_element(By.CSS_SELECTOR, "a.product-name")
                name = driver.execute_script("return arguments[0].innerText;", name_element).strip()
                # check brand — skip if not in our list

                brand = detect_brand(name)
                if brand is None:
                    continue

                #brand = "Unknown"

                # price
                try:
                    #price = card.find_element(By.CSS_SELECTOR, "div.product-price").text.strip()
                    price_element = card.find_element(By.CSS_SELECTOR, ".product-price")
                    price = driver.execute_script("return arguments[0].innerText;", price_element).strip()
                except:
                    price = "N/A"

                # image
                try:
                    img = card.find_element(By.CSS_SELECTOR, "a.product-image img")
                    img_src = img.get_attribute("src")
                    if img_src and not img_src.startswith("http"):
                        image_url = IMAGE_BASE_URL + img_src
                    else:
                        image_url = img_src
                except:
                    image_url = "N/A"

                # url
                try:
                    href = card.find_element(By.CSS_SELECTOR, "a.product-image").get_attribute("href")
                    if href and href.startswith("/"):
                        href = BASE_URL + href
                except:
                    href = "N/A"

                if href in seen_urls:
                    continue

                seen_urls.add(href)
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
    print("Starting anhoch.mk phone scraper...\n")
    phones = scrape_all_phones()

    print(f"\n{'='*50}")
    print(f"Total phones scraped: {len(phones)}")
    print(f"{'='*50}")
    for brand in BRANDS:
        count = len([p for p in phones if p.brand == brand])
        print(f"  {brand}: {count} phones")
    print()
    for phone in phones:
        print(phone)