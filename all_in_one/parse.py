import csv
import os
from dataclasses import dataclass, fields, astuple
from typing import List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


HOME_URL = "https://webscraper.io/test-sites/e-commerce/allinone/"
DATA_PATH = "all_in_one/products/"


PAGES = {
    "home": HOME_URL,
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "phones": urljoin(HOME_URL, "phones/touch"),
}


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
        num_of_reviews=int(
            product_soup.select_one(".ratings > p.pull-right").text.split()[0]
        ),
    )


def get_page_products(url: str) -> List[Product]:
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    all_products = soup.select(".thumbnail")  # css-selectors

    return [parse_single_product(product_soup=product) for product in all_products]


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
        page_products = get_page_products(page_url)
        print("Page:", page, page_products)
        write_products_to_csv(page, page_products)


def main():
    # 1. Check API - does not exists
    # 2. CSS-selectors
    # 3. Attrs
    get_all_products()


if __name__ == "__main__":
    main()
