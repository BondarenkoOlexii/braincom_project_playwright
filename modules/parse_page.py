"""
Product search.

Opens the site, types a search query and returns the URL of the first
found product page.

"""


def search_product(page, URL, query):

    page.context.set_extra_http_headers({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36",
        "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7"
    })

    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(1500)

    search_input = page.locator("xpath=//input[@class='quick-search-input'] >> visible=true").first

    search_input.wait_for(state="visible", timeout=10000)
    search_input.click()

    search_input.press_sequentially(query, delay=80)

    search_input.press("Enter")

    product_link = page.locator(
        "xpath=//div[contains(@class, 'product-wrapper')]//a"
    ).first

    product_link.wait_for(state="attached")

    product_url = product_link.get_attribute("href")

    print(product_url)

    return product_url
