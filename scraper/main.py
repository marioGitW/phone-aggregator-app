import json
from phone_scraper_ananas import scrape_all_phones as scrape_ananas
from phone_scraper_anhoch import scrape_all_phones as scrape_anhoch
from phone_scraper_ledikom import scrape_ledikom as scrape_ledikom
from phone_scraper_neptun import scrape_all_phones as scrape_neptun
from phone_scraper_setec import scrape_all_phones as scrape_setec
from phone_scraper_tehnomarket import scrape_all_phones as scrape_tehnomarket

OUTPUT_FILE = "phones.json"

def phone_to_dict(phone, source):
    return {
        "name":phone.name,
        "brand":phone.brand,
        "price":str(phone.price).strip() if phone.price is not None else "N/A",
        "image_url":phone.image_url,
        "url":phone.url,
        "source":source
    }


def save_to_json(phones, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(phones, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(phones)} phones to {filepath}")


if __name__ == "__main__":

    all_phones = []
    scrapers = [
        ("ananas",scrape_ananas),
        ("anhoch",scrape_anhoch),
        ("ledikom",scrape_ledikom),
        ("neptun",scrape_neptun),
        ("setec",scrape_setec),
        ("tehnomarket",scrape_tehnomarket),
    ]

    for source, scrape_fn in scrapers:
        print(f"\n{'='*50}")
        print(f"Scraping {source}...")
        print(f"{'='*50}")
        try:
            phones = scrape_fn()
            all_phones.extend([phone_to_dict(p, source) for p in phones])
            print(f"Done! Got {len(phones)} phones from {source}")
        except Exception as e:
            print(f"ERROR scraping {source}: {e}")

    print(f"\n{'='*50}")
    print(f"Total phones scraped: {len(all_phones)}")
    print(f"{'='*50}")

    save_to_json(all_phones, OUTPUT_FILE)

    # --- send post request to backend when spring app is made---
    # import requests
    # response = requests.post("http://localhost:8080/api/phones", json=all_phones)
    # print(f"Backend response: {response.status_code}")