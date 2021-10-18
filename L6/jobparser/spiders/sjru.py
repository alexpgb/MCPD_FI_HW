import scrapy
from scrapy.http import HtmlResponse
from jobparser.items import JobparserItem


class SjruSpider(scrapy.Spider):
    name = 'sjru'
    allowed_domains = ['superjob.ru']
    start_urls = ['https://www.superjob.ru/vacancy/search/?keywords=аналитик Data science python'
                  '&geo[t][0]=4&geo[t][1]=33&geo[t][2]=1250']

    def parse(self, response):
        links = response.xpath("//div[@class='f-test-search-result-item']/descendant::"
                               "a[contains(@href, '/vakansii')][1]/@href").getall()
        next_page = response.xpath("//span[text()='Дальше']/ancestor::a[@rel='next']/@href").get()
        if next_page:
            # result_next_page = response.follow(next_page, callback=self.parse)
            yield response.follow(next_page, callback=self.parse)

        for link in links:
            # result_link = response.follow(link, callback=self.vacancy_parse)
            yield response.follow(link, callback=self.vacancy_parse)

    def vacancy_parse(self, responce: HtmlResponse):
        print()
        data_title = responce.xpath('//h1/text()').get()
        data_salary = ' '.join(responce.xpath("//h1/../..//span[contains(@class,'_1OuF_')]//text()").getall())
        data_link = responce.url
        item = JobparserItem(title=data_title, salary=data_salary, url=data_link)
        yield item
