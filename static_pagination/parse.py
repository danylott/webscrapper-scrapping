import csv
import logging
import os
import sys
from dataclasses import dataclass, fields, astuple
from typing import List, Dict
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/static/")
DATA_PATH = "products/"


PAGES = {
    "home": HOME_URL,
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones/touch"),
}

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]:  %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(DATA_PATH, "parser.log")),
        logging.StreamHandler(sys.stdout),
    ],
)

@dataclass
class Product:
    title: str
    description: str
    price: float  # Decimal are also possible if some computations  # in $USD
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=int(product_soup.select_one("p[data-rating]")["data-rating"]),
        num_of_reviews=int(product_soup.select_one(".ratings > p.pull-right").text.split()[0]),
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

    return all_products


def write_products_to_csv(page: str, products: List[Product]):
    with open(os.path.join(DATA_PATH, f"{page}.csv",), "w") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_all_products():
    for page, page_url in PAGES.items():
        category_products = get_category_products(page_url)
        logging.info(f"Successfully parsed: {page} {category_products}")
        write_products_to_csv(page, category_products)


def main():
    # 1. Check API - does not exists
    # 2. CSS-selectors
    # 3. Attrs
    get_all_products()


if __name__ == '__main__':
    main()
