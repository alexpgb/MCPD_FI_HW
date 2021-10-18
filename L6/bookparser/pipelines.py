# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient
import datetime
import pytz
from bookparser.items import BookparserItem


class BookparserPipeline:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        db = client['books']  # выбор БД
        self.db_collection = db.content     # выбор коллекции content
        self.tz_moscow = pytz.timezone('Europe/Moscow')
        self.item_added = 0

    def process_item(self, item: BookparserItem, spider):
        item['createdMSK'] = None
        item['updatedMSK'] = None
        item['software'] = 'scrapy'
        if spider.name == 'book24ru':
            item['title'] = self.process_title(item['title'])
            item['author'] = self.process_str(item['author'])
            item['price'], item['price_val'], item['price_old'] = \
                self.process_price_b24(item['price'], item['price_old'])
            item['url'] = self.process_link(item['url'])
            item['purchases_num'] = self.process_purchases_num(item['purchases_num'])
            item['isbn'] = self.process_str(item['isbn'])

        # Монго реально клевая штука, т.к. не нужно перестраивать БД при изменении структуры собранных данных!!!
        doc_list = list(self.db_collection.find({'url': item['url']}, {'_id': 1, 'createdMSK': 1}))
        if len(doc_list) == 0:
            item['createdMSK'] = datetime.datetime.now(self.tz_moscow)
            new_doc = self.db_collection.insert_one(item)
            self.item_added += 1
        else:
            item['createdMSK'] = doc_list[0]['createdMSK']
            item['updatedMSK'] = datetime.datetime.now(self.tz_moscow)
            new_doc = self.db_collection.replace_one({'_id': doc_list[0]['_id']}, item)
        print()

        return item

    def process_title(self, title):
        if title is not None:
            if ':' in title:
                 title = ':'.join(title.split(':')[1:])
            title = self.process_str(title)
        return title

    def process_price_b24(self, price, price_old):
        # 383 ₽
        price_val = None
        if price:
            price_val = price.split()[1]
            price = int(price.split()[0])
        if price_old:
            price_old = int(price_old.split()[0])
        return price, price_val, price_old

    def process_purchases_num(self, purchases_num):
        # Купили 109 раз
        if purchases_num:
            purchases_num = int(purchases_num.split()[1])
        return purchases_num

    def process_str(self, var_str):
        if var_str is not None:
            var_str = ' '.join(var_str.split()).strip()
        return var_str

    def process_link(self, link):
        if link is not None:
            link = link.split('?')[0]
        return link
