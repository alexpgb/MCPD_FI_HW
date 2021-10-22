import scrapy
from scrapy.http import HtmlResponse
from product_photos.items import ProductPhotosItem
from scrapy.loader import ItemLoader


class LeroymerlinruSpider(scrapy.Spider):
    name = 'leroymerlinru'
    allowed_domains = ['leroymerlin.ru']

    def __init__(self, query):
        super().__init__()
        self.start_urls = [f'https://leroymerlin.ru/search/?q={query}']
        self.page_num = 1

    def parse(self, response: HtmlResponse):
        print()
        # Можно выделять не ссылки, а объект, содержащий ссылки и передавать его в response.follow
        # будут извлечены ссылки из тега a
        # links запишутся объекты
        # links = response.xpath("//div[@data-qa-product]/a[@data-qa-product-image]")
        links = response.xpath("//div[@data-qa-product]/a[@data-qa-product-image]/@href").getall()
        next_page = response.xpath(
            "//div[@role='navigation']//a[contains(@data-qa-pagination-item,'right')]/@href").get()
        if next_page:
            self.page_num += 1
            print(f'self.page_num {self.page_num}  next_page {next_page}')
            yield response.follow(next_page, callback=self.parse)
        for link in links:
            yield response.follow(link, callback=self.item_parse)

    def item_parse(self, response: HtmlResponse):
        loader = ItemLoader(item=ProductPhotosItem(), response=response)
        # если селектор ничего не вернет, то поле в item не будет создано!!! И pipeline грохнется.
        # наверно есть смысл говорить об этом на лекции.
        loader.add_value('url', response.url)
        loader.add_value('rating', None)
        loader.add_xpath('title', "//h1[@slot='title']/text()")
        loader.add_xpath('specifications_keys', "//uc-pdp-section-vlimited/dl/div[@class='def-list__group']//dt/text()")
        loader.add_xpath('specifications_vals', "//uc-pdp-section-vlimited/dl/div[@class='def-list__group']//dd/text()")
        loader.add_xpath('price', "//uc-pdp-price-view//span/text()")
        loader.add_xpath('path_to_prod_in_site', "//uc-breadcrumbs-row//uc-breadcrumbs-link/a/@data-division")
        loader.add_xpath('article_number', "//span[@slot='article']/text()")
        loader.add_xpath('photos', "//uc-pdp-media-carousel//picture[@slot='pictures']"
                                   "/source[contains(@media,'only screen and (min-width: 768px)')]/@srcset")


        # data_title = response.xpath("//h1[@slot='title']/text()").get()
        # data_specifications_keys = response.xpath(
        #     "//uc-pdp-section-vlimited/dl/div[@class='def-list__group']//dt/text()").getall()
        # data_specifications_vals = response.xpath(
        #     "//uc-pdp-section-vlimited/dl/div[@class='def-list__group']//dd/text()").getall()
        # data_price = response.xpath("//uc-pdp-price-view//span/text()").getall()
        # запишем сюда путь в каталоге товаров до товара
        # ['Главная', 'Каталог', 'Окна и двери', 'Двери', 'Входные двери']
        # data_path_to_prod_in_site = response.xpath("//uc-breadcrumbs-row//uc-breadcrumbs-link/a/@data-division").getall()
        #data_url = response.url
        # data_rating = None  # рейтинг спрятан в shadow и не понятно как получить к нему доступ.
        # data_article_number = response.xpath("//span[@slot='article']/text()").get()
        # data_photos = response.xpath("//uc-pdp-media-carousel//picture[@slot='pictures']"
        #                             "/source[contains(@media,'only screen and (min-width: 768px)')]/@srcset").getall()
        # сделаем так сейчас, чтоб можно было контролировать результат
        # item = ProductPhotosItem(title=data_title,
        #                          specifications=data_specifications,
        #                          price=data_price,
        #                          path_to_prod_in_site=data_path_to_prod_in_site,
        #                          url=data_url,
        #                          rating=data_rating,
        #                          article_number=data_article_number,
        #                          photos=data_photos)
        # yield item  # здесь работает return т.к. не нужно замораживать выполнение функции
        yield loader.load_item()  # здесь тоже можно сделать return
