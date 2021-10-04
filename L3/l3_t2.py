from pprint import pprint
from pymongo import MongoClient

while True:
    salary_searched = input('Укажите искомую величину зарплаты (q-выход): ')
    if salary_searched == 'q':
        break
    if not salary_searched.isdigit():
        print('Укажите число')
        continue
    salary_searched = int(salary_searched)
    with MongoClient('localhost', 27017) as client:
        db = client['vacancy']
        col_hh = db.content
        item_find = 0
        doc_list_cursor = col_hh.find({'$or': [{'salary_min': {'$lt': salary_searched}},
                                               {'salary_max': {'$gte': salary_searched}}]},
                                      {'_id': 0})
        pass

        for doc in doc_list_cursor:
            pprint(doc)
            item_find += 1

        print(f'Найдено {item_find} вакансий')


print('End')
