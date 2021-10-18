import scrapy
from scrapy.http import HtmlResponse
from jobparser.items import JobparserItem
import datetime


class HhruSpider(scrapy.Spider):
    name = 'hhru'
    allowed_domains = ['hh.ru']
    # start_urls = ['https://pyshma.hh.ru/search/vacancy?clusters=true&area=1&ored_clusters=true&enable_snippets=true'
    #               '&salary=&st=searchVacancy&text=pyhon+data+sciense&items_on_page=10']
    start_urls = ['https://pyshma.hh.ru/search/vacancy?clusters=true&area=1&ored_clusters=true&items_on_page=10&'
                  'enable_snippets=true&salary=&text=Python+data+science+екатеринбург&from=suggest_post']

    def parse(self, response: HtmlResponse):
        #links = response.xpath("//a[@data-qa='vacancy-serp__vacancy-title']/@href").getall()
        links = response.xpath("//a[@data-qa='vacancy-serp__vacancy-title']/@href").extract()
        next_page = response.xpath("//a[@data-qa='pager-next']/@href").extract_first()
        if next_page:
            # result_next_page = response.follow(next_page, callback=self.parse)
            yield response.follow(next_page, callback=self.parse)

        for link in links:
            # result_link = response.follow(link, callback=self.vacancy_parse)
            yield response.follow(link, callback=self.vacancy_parse)


    def vacancy_parse(self, responce: HtmlResponse):
        print()
        data_title = responce.xpath('//h1/text()').extract_first()
        data_salary = ''.join(responce.xpath("//p[@class='vacancy-salary']/span/text()").extract())
        data_link = responce.url
        item = JobparserItem(title=data_title, salary=data_salary, url=data_link)
        yield item


