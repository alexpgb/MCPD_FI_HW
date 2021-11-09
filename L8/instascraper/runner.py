from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from instascraper import settings
from instascraper.spiders.insta_spider1 import InstaSpider1Spider


if __name__ == '__main__':
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)
    process =CrawlerProcess(settings=crawler_settings)
    process.crawl(InstaSpider1Spider)
    process.start()
