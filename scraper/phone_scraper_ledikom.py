from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


BASE_URL = "https://ledikom.mk"

BRAND_URLS = {
    "Apple": "https://ledikom.mk/c/416/telefoni/apple-iphone",
    "Samsung": "https://ledikom.mk/c/421/telefoni/samsung",
    "Xiaomi": "https://ledikom.mk/c/424/telefoni/xiaomi",
    "Google": "https://ledikom.mk/c/413/telefoni/google",
    "Honor": "https://ledikom.mk/c/411/telefoni/honor",
    "OnePlus": "https://ledikom.mk/c/441/telefoni/oneplus",
}


class Phone:
    def __init__(self, name, brand, price, image_url, url):
        self.name = name
        self.brand = brand
        self.price = price
        self.image_url = image_url
        self.url = url

    def __repr__(self):
        return (f"Phone(name={self.name}, brand={self.brand}, "
                f"price={self.price}, image_url={self.image_url}, url={self.url})")


def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def wait_for_products(driver, timeout=15):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "item-in-grid"))
        )
        time.sleep(2)
        return True
    except:
        return False


def scrape_ledikom():
    driver = get_driver()
    phones = []
    seen_urls = set()

    for brand, url in BRAND_URLS.items():
        print(f"\nScraping {brand} -> {url}")
        driver.get(url)

        loaded = wait_for_products(driver)
        if not loaded:
            print(f"No products found for {brand}")
            continue

        products = driver.find_elements(By.CLASS_NAME, "item-in-grid")
        print(f"Found {len(products)} {brand} phones")

        for p in products:
            try:
                name = p.find_element(By.CSS_SELECTOR, ".item-name a").text.strip().lower()

                # price
                try:
                    price_text = p.find_element(By.CSS_SELECTOR, ".grid-new-price").text
                except:
                    price_text = p.find_element(By.CSS_SELECTOR, ".price").text

                price = (
                    price_text.replace("ден", "")
                    .replace(".", "")
                    .strip()
                )
                price = int(price)

                # image
                image = p.find_element(By.CSS_SELECTOR, ".item-img img").get_attribute("src")

                # link
                link = p.find_element(By.CSS_SELECTOR, "a[href*='/p/']").get_attribute("href")

                if link in seen_urls:
                    continue
                seen_urls.add(link)

                phones.append(Phone(
                    name=name,
                    brand=brand.lower(),
                    price=price,
                    image_url=image,
                    url=link
                ))

                print(f"  + {name} – {price}")

            except Exception as e:
                print("  Skipped product:", e)

    driver.quit()
    return phones


if __name__ == "__main__":
    print("Starting Ledikom scraper...\n")
    phones = scrape_ledikom()

    print(f"\n{'='*50}")
    print(f"Total phones scraped: {len(phones)}")
    print(f"{'='*50}")
    for brand in BRAND_URLS.keys():
        count = len([p for p in phones if p.brand == brand.lower()])
        print(f"  {brand}: {count} phones")
    print()
    for phone in phones:
        print(phone)