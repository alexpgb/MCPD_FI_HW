# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class JobparserItem(scrapy.Item):
    # define the fields for your item here like:
    _id = scrapy.Field()
    site = scrapy.Field()
    software = scrapy.Field()
    title = scrapy.Field()
    salary = scrapy.Field()
    salary_min = scrapy.Field()
    salary_max = scrapy.Field()
    salary_currency = scrapy.Field()
    salary_gross_net = scrapy.Field()
    salary_period = scrapy.Field()
    url = scrapy.Field()
    createdMSK = scrapy.Field()
    updatedMSK = scrapy.Field()
    pass
