"""
Step 2: product page parsing.

Gets a product URL (from search_product.py), opens the page, collects name,
prices, product code, reviews count, photos and characteristics, then saves
the result to the Product table via Django ORM.

"""


from modules.parse_page import search_product
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from load_django import *
from parser_app.models import Product


def get_characteristics(page):
    rows_xpath = (
        "//div[contains(@class,'br-pr-chr-wrap')]"
        "//div[contains(@class,'br-pr-chr-item')]/div/div[count(span)=2]"
    )

    rows = page.locator(f"xpath={rows_xpath}")

    try:
        rows.first.wait_for(state="attached")
    except PlaywrightTimeoutError:
        return {}

    characteristics = {}

    for i in range(rows.count()):
        row = rows.nth(i)

        spans = row.locator("xpath=./span")

        if spans.count() < 2:
            continue

        key = " ".join(
            (spans.nth(0).text_content() or "").split()
        )

        value = " ".join(
            (spans.nth(1).text_content() or "").split()
        )

        if key:
            characteristics[key] = value or None

    return characteristics


def get_photo(page):
    photos_xpath = (
        "//div[contains(@class,'br-image-links')]"
        "/div[contains(@class,'slick-list draggable')]//img"
    )

    images = page.locator(f"xpath={photos_xpath}")

    url_photos = []

    for i in range(images.count()):
        img = images.nth(i)

        img_src = img.get_attribute("src")

        if img_src:
            url_photos.append(img_src)

    return url_photos


def work_with_product(page, url):
    page.goto(url)

    product = {}

    characteristics = get_characteristics(page)

    try:
        product["name"] = page.locator(
            "xpath=//h1[@class='desktop-only-title']"
        ).inner_text()

    except PlaywrightTimeoutError:
        product["name"] = None

    try:
        product["regular_price"] = (
            page.locator("xpath=//div[contains(@class, 'main-price-block')]//div/span").text_content().replace(" ", "")
            .replace(" ", "")
        )

    except PlaywrightTimeoutError:
        product["regular_price"] = None

    try:
        product["promotion_price"] = (
            page.locator(
                "xpath=//div[contains(@class, 'main-price-block')]//div/span[@class='red-price']")
            .inner_text()
            .replace(" ", "")
            .strip()
            or None
        )

    except PlaywrightTimeoutError:
        product["promotion_price"] = None

    try:
        product["code"] = (
            page.locator(
                "xpath=//div[contains(@class, 'main-right-block')]"
                "//span[contains(@class, 'br-pr-code-val')]"
            ).inner_text()
            .strip()
        )

    except PlaywrightTimeoutError:
        product["code"] = None

    try:
        reviews_xpath = (
            "//div[contains(@class, 'br-pt-rt-main-mark')]"
            "/div/a[contains(@class, 'scroll-to-element')]"
        )

        product["numb_of_reviews"] = (
            page.locator(
                f"xpath={reviews_xpath}"
            ).inner_text()
        )

    except PlaywrightTimeoutError:
        product["numb_of_reviews"] = None

    product["photos"] = get_photo(page)

    product["color"] = characteristics.get("Колір")
    product["storage"] = characteristics.get("Вбудована пам'ять")
    product["manufacturer"] = characteristics.get("Виробник")
    product["display_resolution"] = characteristics.get("Роздільна здатність екрану")
    product["screen_diagonal"] = characteristics.get("Діагональ екрану")

    product["product_specification"] = characteristics

    return product


if __name__ == "__main__":
    URL = ("https://brain.com.ua/ ")

    PROFILE_DIR = "chrome_profile"

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            channel="chrome",
            headless=False,
            locale="uk-UA",
            viewport={"width": 1920, "height": 1080},
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
        )

        page = context.pages[0] if context.pages else context.new_page()

        try:
            product_url = search_product(page, URL, "Apple iPhone 15 128GB Black")

            product = work_with_product(
                page,
                url=product_url
            )
        finally:
            context.close()

    for key, value in product.items():
        print(f"{key} - {value}" "\n")

    Product.objects.get_or_create(
        name=product["name"],
        color=product["color"],
        storage=product["storage"],
        manufacturer=product["manufacturer"],
        regular_price=product["regular_price"],
        promotion_price=product["promotion_price"],
        photos=product["photos"],
        code=product["code"],
        numb_of_reviews=product["numb_of_reviews"],
        display_resolution=product["display_resolution"],
        screen_diagonal=product["screen_diagonal"],
        product_specification=product["product_specification"]
    )
