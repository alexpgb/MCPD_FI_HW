from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from product_photos import settings
from product_photos.spiders.leroymerlinru import LeroymerlinruSpider


if __name__ == '__main__':
    #search_text = 'двери'
    search_text = 'двери&page=48'
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)
    process = CrawlerProcess(settings=crawler_settings)
    process.crawl(LeroymerlinruSpider, query=search_text)
    process.start()

