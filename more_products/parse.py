import csv
import time
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

BASE_URL = "https://webscraper.io/"
HOME_URL = urljoin(BASE_URL, "test-sites/e-commerce/more/")

PAGES = {
    "home": HOME_URL,
    "computers": urljoin(HOME_URL, "computers"),
    "phones": urljoin(HOME_URL, "phones"),
    "laptops": urljoin(HOME_URL, "computers/laptops"),
    "tablets": urljoin(HOME_URL, "computers/tablets"),
    "touch": urljoin(HOME_URL, "phones/touch"),
}


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=len(product_soup.select(".glyphicon-star")),
        num_of_reviews=int(
            product_soup.select_one(".ratings > p.pull-right").text.split()[0]
        ),
    )


def get_element_or_none(driver, class_name: str) -> WebElement | None:
    try:
        return driver.find_element(By.CLASS_NAME, class_name)
    except NoSuchElementException:
        return None


def check_and_click_cookies_button(driver: WebDriver) -> None:
    if cookie_button := get_element_or_none(driver, "acceptCookies"):
        time.sleep(0.1)

        if cookie_button.is_displayed():
            cookie_button.click()


def show_all_products(driver: WebDriver) -> None:
    while True:
        check_and_click_cookies_button(driver)

        more_button = get_element_or_none(driver, "ecomerce-items-scroll-more")
        time.sleep(0.1)
        if not more_button or not more_button.is_displayed():
            break

        more_button.click()


def get_page_products(driver: WebDriver, url: str) -> list[Product]:
    driver.get(url)
    time.sleep(0.5)
    show_all_products(driver)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    all_products = soup.select(".thumbnail")

    return [parse_single_product(product_soup=product) for product in all_products]


def get_all_products() -> list[Product]:
    all_products = []

    with webdriver.Chrome() as driver:
        for page_name, page_url in PAGES.items():
            products = get_page_products(driver, page_url)
            all_products.extend(products)
            write_products_to_csv(page_name, products)

    return all_products


def write_products_to_csv(page_name: str, products: list[Product]):
    with open(f"{page_name}.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def main():
    print(get_all_products())


if __name__ == "__main__":
    main()
