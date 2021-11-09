# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import datetime
from pymongo import MongoClient
import pytz


class InstascraperPipeline:
    def __init__(self):
        client = MongoClient('localhost', 27017)
        db = client['instagram']  # выбор БД
        self.db_collection = db.content     # выбор коллекции content
        self.tz_moscow = pytz.timezone('Europe/Moscow')
        self.item_added = 0

    def process_item(self, item, spider):
        # разбирать закрыт ли аккаунт
        item['createdMSK'] = None
        item['updatedMSK'] = None
        item['software'] = 'scrapy'
        if spider.name == 'insta_spider1':
            # ничего не будем делать в pipeline
            item['friend_id'] = str(item['friend_id'])  # иначе не влазит в mongodb
            pass
        # Есть ли тот, на кого подписываются
        doc = {'software': item['software']}
        for i in range(2): # добавим пользователя и его френда
            if i == 0: # добавим пользователя
                doc = {'user_id': item['user_id'],
                       'user_name': item['user_name'],
                       'user_data' : item['user_data']}
            elif i == 1: # добавим френда
                doc = {'user_id': item['friend_id'],
                       'user_name': item['friend_name'],
                       'user_data': item['friend_data']}  # тут может быть ситуация, когда добавляем информацию по френду, затрем информацию по юзеру, которая более полная.
                                                          # но пока забъем на это.
            doc_list = list(self.db_collection.find({'user_id': doc['user_id']}, {'_id': 1, 'createdMSK': 1,
                                                                                  'followers': 1, 'following': 1})) # возвращается объект курсор
            if len(doc_list) == 0:
                doc['createdMSK'] = datetime.datetime.now(self.tz_moscow)
                doc['updatedMSK'] = item['updatedMSK']
                doc['followers'] = []
                doc['following'] = []
                new_doc = self.db_collection.insert_one(doc)
                self.item_added += 1
            else:
                doc['createdMSK'] = doc_list[0]['createdMSK']
                doc['updatedMSK'] = datetime.datetime.now(self.tz_moscow)
                new_doc = self.db_collection.update_one({'_id': doc_list[0]['_id']}, {'$set': doc})  # не очень красиво, что мы обновляем вместе с user_id, но пусть будет пока так.
        # дополним подписки
        # тут не получится контролировать ситуацию, когда кто то удаляется из подписчиков или удаляет подписки.
        # т.к. в items нужно передвать полный список, чтобы его полностью апдейтить. Поэтому только добавление.
        if item['friend_type'] == 'follower':
            # получим список френдов
            doc_list = list(self.db_collection.find({'user_id': item['user_id']}, {'_id': 0, 'followers': 1}))
            if item['friend_id'] not in doc_list[0]['followers']: # если подписчик есть в списке подписчиков
                new_doc = self.db_collection.update_one({'user_id': item['user_id']}, {'$push': {'followers': item['friend_id']}})
            # получим спиcок подписок у френда
            doc_list = list(self.db_collection.find({'user_id': item['friend_id']}, {'_id': 0, 'following': 1}))
            if item['user_id'] not in doc_list[0]['following']: # если юзер есть в списке подписок
                new_doc = self.db_collection.update_one({'user_id': item['friend_id']}, {'$push': {'following': item['user_id']}})
        elif item['friend_type'] == 'following':
            # получим список френдов
            doc_list = list(self.db_collection.find({'user_id': item['user_id']}, {'_id': 0, 'following': 1}))
            if item['friend_id'] not in doc_list[0]['following']: # если подписчик есть в списке подписчиков
                new_doc = self.db_collection.update_one({'user_id': item['user_id']}, {'$push': {'following': item['friend_id']}})
            # получим спиcок подписок у френда
            doc_list = list(self.db_collection.find({'user_id': item['friend_id']}, {'_id': 0, 'followers': 1}))
            if item['user_id'] not in doc_list[0]['followers']: # если подписчик есть в списке подписчиков
                new_doc = self.db_collection.update_one({'user_id': item['friend_id']}, {'$push': {'followers': item['user_id']}})
        print()
        return item
