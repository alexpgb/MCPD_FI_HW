# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html


import scrapy
from itemloaders.processors import MapCompose, TakeFirst, Compose # Compose - обрабатывает единичное значение


# преобработчик применится сразу после выбор селектора
# постобраотчик срабатывает, все поля уже загружены и вызван метод load_item в loader
# например можем подменить ссылку на скачивание с маленькой картинки на большую (подмена буквы).

def clear_str(value):
    if value is not None:
        try:
            value = ' '.join(value.split())
        except:
            return value
    return value


def process_link(link):
    if link is not None:
        link = link.split('?')[0]
    return link


class ProductPhotosItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # _id = scrapy.Field()
    # createdMSK = scrapy.Field()
    # updatedMSK = scrapy.Field()
    software = scrapy.Field()
    site = scrapy.Field()
    title = scrapy.Field(input_processor=MapCompose(clear_str), output_processor=TakeFirst())
    specifications = scrapy.Field()
    specifications_keys = scrapy.Field(input_processor=MapCompose(clear_str))
    specifications_vals = scrapy.Field(input_processor=MapCompose(clear_str))
    price = scrapy.Field(input_processor=MapCompose(clear_str))
    price_val = scrapy.Field()
    price_measure_unit = scrapy.Field()
    type = scrapy.Field()
    path_to_prod_in_site = scrapy.Field(input_processor=MapCompose(clear_str))
    path_to_photo = scrapy.Field()
    url = scrapy.Field(input_processor=MapCompose(process_link), output_processor=TakeFirst())
    rating = scrapy.Field()
    article_number = scrapy.Field(input_processor=MapCompose(clear_str), output_processor=TakeFirst())
    photos = scrapy.Field()
    pass
