# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BookparserItem(scrapy.Item):
    # define the fields for your item here like:
    _id = scrapy.Field()
    createdMSK = scrapy.Field()
    updatedMSK = scrapy.Field()
    software = scrapy.Field()
    title = scrapy.Field()
    author = scrapy.Field()
    price = scrapy.Field()
    price_old = scrapy.Field()
    price_val = scrapy.Field()
    url = scrapy.Field()
    purchases_num = scrapy.Field()
    isbn = scrapy.Field()
    pass
