from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

BASE_URL = "https://setec.mk"
CATEGORY_URL = (
    "https://setec.mk/category/mobilni-20telefoni-67?"
    "sort=%25D0%259D%25D0%25B0%25D1%2598%25D0%25B5%25D0%25B2%25D1%2582%25D0%25B8%25D0%25BD%25D0%25BE"
    "&minPrice=2995"
    "&maxPrice=164990"
    "&%25D0%2591%25D1%2580%25D0%25B5%25D0%25BD%25D0%25B4=Apple"
    "&%25D0%2591%25D1%2580%25D0%25B5%25D0%25BD%25D0%25B4=Samsung"
    "&%25D0%2591%25D1%2580%25D0%25B5%25D0%25BD%25D0%25B4=Xiaomi"
    "&%25D0%2591%25D1%2580%25D0%25B5%25D0%25BD%25D0%25B4=Honor"
)

BRANDS = ["apple", "samsung", "xiaomi", "honor"]

NAME_PREFIXES = [
    "преднарачка -",
    "мобилен телефон",
    "паметен телефон",
    "mobile phone",
    "smartphone"
]
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
    driver = webdriver.Chrome(options=options)
    return driver


def wait_for_cards(driver, timeout=15):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.relative.bg-white.p-4.rounded-\\[20px\\]")
            )
        )
        time.sleep(2)
        return True
    except:
        return False


def detect_brand(name):
    name_lower = name.lower()
    for brand in BRANDS:
        if brand.lower() in name_lower:
            return brand
    return None

def clean_name(name):
    name = name.lower().strip()
    # remove known prefixes anywhere in the name
    for prefix in NAME_PREFIXES:
        name = name.replace(prefix, "").strip()
    # remove anything inside parentheses including the parentheses themselves
    name = re.sub(r'\(.*?\)', '', name).strip()
    # clean up any double spaces left behind
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def scrape_all_phones():
    driver = get_driver()
    phones = []
    seen_urls = set()
    page = 1

    while True:
        url = f"{CATEGORY_URL}&page={page}"
        print(f"Scraping page {page} -> {url}")
        driver.get(url)

        loaded = wait_for_cards(driver)
        if not loaded:
            print(f"No products on page {page}, stopping.")
            break

        products = driver.find_elements(
            By.CSS_SELECTOR,
            "div.relative.bg-white.p-4.rounded-\\[20px\\]"
        )

        print(f"Found {len(products)} products on page {page}")

        if not products:
            break

        for p in products:
            try:
                raw_name = p.find_element(By.TAG_NAME, "h3").text.strip()
                link = p.find_element(By.TAG_NAME, "a").get_attribute("href")

                if link in seen_urls:
                    continue
                seen_urls.add(link)

                # image
                image = p.find_element(By.CSS_SELECTOR, "img[alt]").get_attribute("src")
                name = clean_name(raw_name)
                # brand detection (name MUST contain one of the brands)
                brand = detect_brand(name)
                if brand is None:
                    continue


                try:
                    price_container = p.find_element(
                        By.XPATH,
                        ".//p[contains(., 'Клуб цена')]"
                    )
                    price_text = price_container.find_elements(By.TAG_NAME, "span")[1].text
                except:
                    price_text = p.find_element(
                        By.XPATH,
                        ".//p[contains(., 'Редовна цена')]"
                    ).text

                price = int(re.sub(r"\D", "", price_text))

                phones.append(Phone(
                    name=name,
                    brand=brand,
                    price=price,
                    image_url=image,
                    url=link
                ))

                print(f"  + [{brand}] {name} – {price}")

            except Exception as e:
                print("  Skipped a product:", e)

        page += 1

    driver.quit()
    return phones


if __name__ == "__main__":
    print("Starting setec.mk phone scraper...\n")
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