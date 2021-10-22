# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import scrapy
from itemadapter import ItemAdapter
from pymongo import MongoClient
import datetime
import pytz
from product_photos.items import ProductPhotosItem
from scrapy.pipelines.images import ImagesPipeline
#import os
from urllib.parse import urlparse
import hashlib
from scrapy.utils.python import to_bytes



class ProductPhotosPipelineSaveItem:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        db = client['products']  # выбор БД
        self.db_collection = db.content     # выбор коллекции content
        self.tz_moscow = pytz.timezone('Europe/Moscow')
        self.item_added = 0

    def process_item(self, item, spider):
        doc = {k: item[k] for k in item.keys() if k not in ['path_to_prod_in_site',
                                                            'specifications_keys',
                                                            'specifications_vals',
                                                            'path_to_photo']} # отброосим не нужные поля
        doc['createdMSK'] = None
        doc['updatedMSK'] = None
        doc_list = list(self.db_collection.find({'url': doc['url']}, {'_id': 1, 'createdMSK': 1}))
        if len(doc_list) == 0:
            doc['createdMSK'] = datetime.datetime.now(self.tz_moscow)
            new_doc = self.db_collection.insert_one(doc)
            self.item_added += 1
        else:
            doc['createdMSK'] = doc_list[0]['createdMSK']
            doc['updatedMSK'] = datetime.datetime.now(self.tz_moscow)
            new_doc = self.db_collection.replace_one({'_id': doc_list[0]['_id']}, doc)
        print()


class ProductPhotosPipeline:
    def process_item(self, item, spider):
        item['software'] = 'scrapy'
        if spider.name == 'leroymerlinru':
            item['site'] = item['url'].split('/')[2]
            #item['title'] = self.process_title(item['title'])
            #item['title'] = ' '.join(item['title'].split())
            item['price'], item['price_val'], item['price_measure_unit'] = self.process_price_lm(item['price'])
            #item['url'] = self.process_link(item['url'])
            item['type'] = self.process_type_lm(item['path_to_prod_in_site'])  # вид товара; достаем последний элемент
            item['rating'] = None
            item['article_number'] = item['article_number'].split()[1]
            item['specifications'] = self.process_spec_lm(item['specifications_keys'], item['specifications_vals'])
            item['path_to_photo'] = self.create_path_to_photo_by_prod_name(item['path_to_prod_in_site'], item['title'])
            # item['photos']
        return item

    def create_path_to_photo_by_prod_name(self, path_to_prod_in_site, title):
        path_to_photo = None
        if path_to_prod_in_site is not None and title is not None:
            if len(path_to_prod_in_site) > 0:
                path_to_photo = [self.str_translit_gost(val.strip().replace(',', '').
                                                        replace('  ', '').replace(' ', '_'))
                                 for val in path_to_prod_in_site if val not in ['Главная', 'Каталог']]
                path_to_photo = '/'.join(path_to_photo)
            path_to_photo = path_to_photo + '/' + self.str_translit_gost(title.replace(',', '')
                                                                          .replace('  ', '').replace(' ', '_'))
        return path_to_photo

    def str_translit_gost(self, str_rus):
        # транслитерация по ГОСТ-а 7.79-2000
        # перепилим функцию с mssql на python
        rus  = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
        lat1 = 'abvgdejzzijklmnoprstufkccss y ejj'
        lat2 = '      oh  j           h hhh   hua'
        lat3 = '                          h      '
        str_lat = ''
        for ch in str_rus:
            pos = rus.find(ch.lower())
            if pos >= 0:
                if ord(ch.upper()) == ord(ch):
                    str_lat = str_lat + lat1[pos:pos + 1].upper() + lat2[pos:pos + 1].strip() + lat3[
                                                                                                pos:pos + 1].strip()
                else:
                    str_lat = str_lat + lat1[pos:pos + 1] + lat2[pos:pos + 1].strip() + lat3[pos:pos + 1].strip()
            else:
                str_lat = str_lat + ch  # встретился символ не русского алфавита
        return str_lat

    def process_spec_lm(self, spec_keys, spec_vals):
        spec_dict = None
        if spec_keys is not None and spec_vals is not None:
            if len(spec_keys) == len(spec_vals) and len(spec_keys) > 0:
                # spec_dict = dict(zip(spec_keys, spec_vals))
                # spec_dict = {' '.join(k.split()): ' '.join(spec_dict[k].split()) for k in spec_dict.keys()}
                spec_dict = {spec_keys[i]: spec_vals[i] for i in range(len(spec_keys))}
        return spec_dict

    def process_price_lm(self, price):
        price_val = None
        price_measure_unit = None
        if price:
            price_val = price[1]
            price_measure_unit = price[2]
            price = int(''.join(price[0].split()))
        return price, price_val, price_measure_unit

    def process_type_lm(self, val):
        if val:
            val = val[-1]
        return val

    def process_str(self, var_str):
        if var_str is not None:
            var_str = ' '.join(var_str.split()).strip()
        return var_str

class ProductPhotosPipelineProc(ImagesPipeline):
    def get_media_requests(self, item, info):
        if item['photos']:
            for link_img in item['photos']:
                try:
                    yield scrapy.Request(link_img)
                except Exception as e:
                    print(f'link:{link_img} error:{e}')

    def item_completed(self, results, item, info):
        # запускается, когда заканчивается скачивание
        if len(results) > 0:
            item['photos'] = [i[1] for i in results if i[0] is True]
        return item


    def file_path(self, request, response=None, info=None, *, item=None):
        # здесь можем кастомизировать имя файла
        # print()
        image_guid = hashlib.sha1(to_bytes(request.url)).hexdigest()
        #return 'files/' + os.path.basename(urlparse(request.url).path)
        # return f'full/{image_guid}.jpg'
        return f"lm/full/{item['path_to_photo']}/{image_guid}.{urlparse(request.url).path.split('.')[-1]}"
