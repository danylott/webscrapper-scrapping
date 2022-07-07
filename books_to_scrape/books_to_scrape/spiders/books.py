import re
from urllib.parse import urljoin

import scrapy
from scrapy.http import Response

global_var = 0


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/"]

    def close(spider, reason):
        print(f"ENDING: {global_var}")

    def parse(self, response: Response, **kwargs):
        books = response.css(".product_pod")
        global global_var
        global_var += len(books)
        for book in books:
            book_detail_url = urljoin(
                response.url, book.css(".product_pod > h3 > a::attr(href)").get()
            )
            yield scrapy.Request(book_detail_url, callback=self.parse_book)

        next_page = response.css(".next > a::attr(href)").get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

    def parse_book(self, response: Response):
        if response.status == 404:
            print(response.url)
            exit(0)
        yield {
            "title": response.css(".product_main > h1::text").get(),
            "price": float(response.css(".price_color::text").get().replace("£", "")),
            "amount_in_stock": int(
                re.findall(
                    r"\d+",
                    "".join(response.css(".instock ::text").getall())
                    .strip()
                    .replace("£", ""),
                )[0]
            ),
            "rating": self._str_to_int(response.css(".star-rating::attr(class)").get().split()[-1]),
            "category": response.css(".breadcrumb > li > a::text")[-1].get(),
            "description": response.css("#product_description + p::text").get(),
            "upc": response.css("td::text")[0].get(),
        }

    def _str_to_int(self, num_str: str) -> int:
        str_to_num_dict = {
            "zero": 0,
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
        }
        return str_to_num_dict[num_str.lower()]
