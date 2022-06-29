import csv
import logging
import os
import sys
from dataclasses import dataclass, astuple, fields
from typing import List, Dict, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/static/")
DATA_PATH = "products/"


PAGES = {
    # "home": HOME_URL,
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    # "tablets": urljoin(HOME_URL, "computers/tablets"),
    # "phones": urljoin(HOME_URL, "phones/touch"),
}

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]:  %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(DATA_PATH, "parser.log")),
        logging.StreamHandler(sys.stdout),
    ],
)

_driver: Optional[WebDriver] = None


def get_driver() -> WebDriver:
    return _driver


def set_driver(new_driver: WebDriver) -> None:
    global _driver
    _driver = new_driver


@dataclass
class Product:
    title: str
    description: str
    price: float  # Decimal are also possible if some computations  # in $USD
    rating: int
    num_of_reviews: int
    additional_info: dict


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_hdd_block_prices(product_soup: BeautifulSoup) -> Dict[str, float]:
    prices = {}
    detailed_url = urljoin(BASE_URL, product_soup.select_one(".title")["href"])

    driver = get_driver()
    driver.get(detailed_url)
    swatches = driver.find_element(By.CLASS_NAME, "swatches")
    buttons = swatches.find_elements(By.TAG_NAME, "button")

    for button in buttons:
        if not button.get_property("disabled"):
            button.click()
            prices[button.get_property("value")] = float(
                driver.find_element(By.CLASS_NAME, "price").text.replace("$", "")
            )

    return prices


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    hdd_prices = parse_hdd_block_prices(product_soup)

    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=int(product_soup.select_one("p[data-rating]")["data-rating"]),
        num_of_reviews=int(
            product_soup.select_one(".ratings > p.pull-right").text.split()[0]
        ),
        additional_info={"hdd_prices": hdd_prices}
    )


def get_num_of_pages(page_soup: BeautifulSoup) -> int:
    pagination = page_soup.select_one(".pagination")

    if pagination is None:
        return 1

    return int(pagination.select("li")[-2].text)


def get_single_page_products(page_soup: BeautifulSoup) -> List[Product]:
    products = page_soup.select(".thumbnail")
    return [parse_single_product(product_soup=product) for product in products]


def get_category_products(url: str) -> List[Product]:
    category_page = requests.get(url)
    soup = BeautifulSoup(category_page.content, "html.parser")

    num_pages = get_num_of_pages(soup)

    all_products = get_single_page_products(soup)

    for page in range(2, num_pages + 1):
        logging.debug(f"Parsing page #{page}")
        page = requests.get(url, params={"page": page})
        soup = BeautifulSoup(page.content, "html.parser")
        all_products.extend(get_single_page_products(soup))
        break

    return all_products


def write_products_to_csv(page: str, products: List[Product]):
    with open(
        os.path.join(
            DATA_PATH,
            f"{page}.csv",
        ),
        "w",
    ) as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products():
    for page, page_url in PAGES.items():
        category_products = get_category_products(page_url)
        logging.info(f"Successfully parsed: {page} {category_products}")
        write_products_to_csv(page, category_products)


def main():
    with webdriver.Chrome() as chrome_driver:
        set_driver(chrome_driver)
        get_all_products()


if __name__ == "__main__":
    main()
