import scrapy
from scrapy.http import HtmlResponse
from bookparser.items import BookparserItem


class Book24ruSpider(scrapy.Spider):
    name = 'book24ru'
    allowed_domains = ['book24.ru']
    #start_urls = ['http://book24.ru/']
    start_urls = ['https://book24.ru/search/?q=data science ML']

    def __init__(self):
        super().__init__()
        self.page_num = 1


    def parse(self, response: HtmlResponse):
        # если через класс не получится опредлелить номер страницы то тогда
        # if 'page_num' not in locals(): page_num = 1
        # else: page_num += 1
        print()
        if response.xpath("//h1[@class='not-found__title']").get() is not None:
            # или можно по коду 404
            print(f'Обнаружили переход на отсутствующую страницу. Конец перебора страниц')
            # или yield или return?
            # а по факту все это чушь,
            # когда приходит response.status = 404 вообще метод parse() не вызвыается!!!!
        else:
            self.page_num += 1
            next_page = f'/search/page-{self.page_num}/?' + response.url.split('?')[1]
            print(f'self.page_num {self.page_num}  next_page {next_page}')
            yield response.follow(next_page, callback=self.parse)
            links = response.xpath("//div[@class='product-list__item']/article/descendant::"
                                   "a[contains(@class, 'product-card')][1]/@href").getall()
            for link in links:
                yield response.follow(link, callback=self.book_parse)
            print()

    def book_parse(self, response: HtmlResponse):
        data_title = response.xpath("//h1[@itemprop='name']/text()").get()
        data_author = response.xpath("//div[contains(@class,'product-characteristic product-detail-page__"
                                     "product-characteristic')]//span[@class='product-characteristic__label' "
                                     "and contains(text(),'Автор')]/../..//a/text()").get()
        data_price = response.xpath("//span[@class='app-price product-sidebar-price__price']/text()").get()
        data_price_old = response.xpath("//span[@class='app-price product-sidebar-price__price-old']/text()").get()
        data_url = response.url
        data_purchases_num = response.xpath("//p[@class='product-detail-page__purchased-text']/text()").get()
        data_isbn = response.xpath("//div[contains(@class,'product-characteristic product-detail-page__"
                                   "product-characteristic')]//span[@class='product-characteristic__label' "
                                   "and contains(text(),'ISBN')]/../..//button/text()").get()
        # сделаем так сейчас, чтоб можно было контролировать результат
        item = BookparserItem(title=data_title,
                              author=data_author,
                              price=data_price,
                              price_old=data_price_old,
                              url=data_url,
                              purchases_num=data_purchases_num,
                              isbn=data_isbn)
        yield item      # здесь работает return т.к. не нужно замораживать выполнение функции
