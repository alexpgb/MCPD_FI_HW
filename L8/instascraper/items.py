# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class InstascraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # _id = scrapy.Field()
    createdMSK = scrapy.Field()
    updatedMSK = scrapy.Field()
    software = scrapy.Field()
    friend_type = scrapy.Field()
    user_id = scrapy.Field()
    user_name = scrapy.Field()
    user_data = scrapy.Field()
    friend_id = scrapy.Field()
    friend_name = scrapy.Field()
    friend_data = scrapy.Field()
    pass
