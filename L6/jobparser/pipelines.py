# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import datetime

from itemadapter import ItemAdapter
from pymongo import MongoClient
import pytz

class JobparserPipeline:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        db = client['vacancy']  # выбор БД
        self.db_collection = db.content     # выбор коллекции content
        self.tz_moscow = pytz.timezone('Europe/Moscow')
        self.item_added = 0

    def process_item(self, item, spider):
        item['createdMSK'] = None
        item['updatedMSK'] = None
        item['software'] = 'scrapy'
        if spider.name == 'hhru':
            item['title'] = self.process_name_hh(item['title'])
            item['salary'], item['salary_min'], item['salary_max'], item['salary_currency'], item['salary_gross_net'] \
                = self.process_salary_hh(item['salary'])
            item['url'] = self.process_link_hh(item['url'])
            item['site'] = 'hh.ru'
        elif spider.name == 'sjru':
            item['title'] = self.process_name_sj(item['title'])
            item['salary'], item['salary_min'], item['salary_max'], item['salary_currency'], \
                          item['salary_gross_net'], item['salary_period'] = self.process_salary_sj(item['salary'])
            item['url'] = self.process_link_sj(item['url'])
            item['site'] = 'superjob.ru'

        # if self.db_collection.count_documents({'url': item['url']}) == 0:  # так не надо, надо достать createdMSK
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

    def process_name_hh(self, name):
        if name is not None:
            name = name.replace('\xa0', ' ')
        return name

    def process_name_sj(self, name):
        if name is not None:
            name = ' '.join(name.split())
        return name

    def process_salary_hh(self, salary):
        # 'от 100\xa0000 до 200\xa0000 руб. на руки'
        # 'до 350 000 руб. до вычета налогов'
        # 'з/п не указана'
        salary_min = None
        salary_max = None
        salary_currency = None
        salary_gross_net = None
        salary_processed = None
        if salary is not None and 'з/п не указана' not in salary:
            salary_processed = ' '.join(salary.split())  # убирает все лишние пробелы и юникод
            if 'на руки' in salary:
                salary_gross_net = 'net'
                salary = salary.replace('на руки', '')
            if 'до вычета налогов' in salary:
                salary_gross_net = 'gross'
                salary = salary.replace('до вычета налогов', '')
            salary_currency = salary.split()[-1]
            salary = salary.replace(salary_currency, '')
            salary = salary.split()
            if 'до' in salary:
                salary_max = int(''.join(salary[salary.index('до') + 1:salary.index('до') + 3]))
            if 'от' in salary:
                salary_min = int(''.join(salary[salary.index('от') + 1:salary.index('от') + 3]))
            if '–' in salary:
                salary_min = int(salary.split()[0])
                salary_max = int(salary.split()[2])
        return salary_processed, salary_min, salary_max, salary_currency, salary_gross_net

    def process_salary_sj(self, salary):
        # 'до 300 000 руб./месяц'
        # '47 000 — 55 000 руб./месяц'
        salary_min = None
        salary_max = None
        salary_currency = None
        salary_gross_net = None
        salary_processed = None
        salary_period = None
        if salary is not None and 'з/п не указана' not in salary:
            salary_processed = ' '.join(salary.split())  # убирает все лишние пробелы и юникод
            if '/' in salary:
                salary_period = salary.split('/')[1].strip()
                salary = salary.split('/')[0]
            if 'на руки' in salary:
                salary_gross_net = 'net'
                salary = salary.replace('на руки', '')
            if 'до вычета налогов' in salary:
                salary_gross_net = 'gross'
                salary = salary.replace('до вычета налогов', '')
            salary_currency = salary.split()[-1]
            salary = salary.replace(salary_currency, '')
            salary = salary.split()
            if 'до' in salary:
                salary_max = int(''.join(salary[salary.index('до') + 1:salary.index('до') + 3]))
            if 'от' in salary:
                salary_min = int(''.join(salary[salary.index('от') + 1:salary.index('от') + 3]))
            # print(salary)
            if '—' in salary:
                salary_min = int(''.join(salary[0:2]))
                salary_max = int(''.join(salary[salary.index('—') + 1:salary.index('—') + 3]))
        return salary_processed, salary_min, salary_max, salary_currency, salary_gross_net, salary_period

    def process_link_sj(self, link):
        if link is not None:
            link = link.split('?')[0]
        return link

    def process_link_hh(self, link):
        if link is not None:
            link = link.split('?')[0]
        return link
