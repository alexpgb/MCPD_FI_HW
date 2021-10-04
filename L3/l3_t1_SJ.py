import requests
# import json
from pathlib import Path
from bs4 import BeautifulSoup as bs
# from pprint import pprint
# import pandas as pd
from pymongo import MongoClient
import os


# search_text = input('Введите строку поиска (слова, разделенные пробелом) :')
search_text = 'аналитик Data science python'
# max_page_num = input('Укажите сколько страниц обработать:')
# search_text = 'Педагог-организатор / Специалист-аналитик по контролю качества обучения'
max_page_num = '1000'
if len(search_text) > 0 and len(max_page_num) > 0:
    max_page_num = int(max_page_num)
    site = 'https://www.superjob.ru'
    access_point = '/vacancy/search'
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/93.0.4577.63 Safari/537.36'}
#    search_text = 'data science python'
    params = {'keywords': search_text,
              'geo[t][0]': 4,  # Москва
              'geo[t][1]': 33,  # Екатеринбург
              'geo[t][2]': 1250  # Верхняя Пышма
              }
    url = site + access_point
    searh_item = {
        'el': 'div',
        'attrs': 'jNMYr GPKTZ _1tH7S'}

    # searh_vacancy_name = [
    #     {'el': 'a', 'attrs': {'class': ['icMQ_', '_6AfZ9', '_2JivQ', '_1UJAN']}},
    #     {'el': 'span', 'attrs': {'class': '_1rS-s'}}]

    searh_name = {'el': 'a', 'attrs': {'class': ['icMQ_', '_6AfZ9', '_2JivQ', '_1UJAN']}}
    searh_url = {'el': 'a',
                 'attrs': {'class': ['icMQ_', '_6AfZ9', '_2JivQ', '_1UJAN']}}
    searh_salary = {
        'el': 'span',
        'attrs': {'class': '_1OuF_ _1qw9T f-test-text-company-item-salary'}}

    searh_button_next = {
        'el': 'a',
        'attrs': {'class': 'icMQ_ bs_sM _3ze9n _2EmPY f-test-button-dalshe f-test-link-Dalshe'}}
    result = {'site': [], 'title': [],
              'salary': [],
              'salary_min': [], 'salary_max': [], 'salary_currency': [], 'salary_payment_frequency': [],
              'url': []
              }
    page_num = 0
    num = 0
    print(f'Текущая директория {os.getcwd()}')
    if os.getcwd().split('\\')[-1].upper() == 'L2':
        os.chdir('..')

    while True:
        page_num += 1
        file_name = rf'.\L2\SJ_pages\hh_response_{page_num}.html'
        if page_num == 1:
            response = requests.get(url, params=params, headers=headers)
        else:
            response = requests.get(url, headers=headers)
        print(response.request.url)
        print(response)
        if response.ok:  # 200..399
            response_txt = response.content
            with open(file_name, 'wb') as f:
                f.write(response_txt)
                f.close()
                print(f'Содержимое запроса сохранено в файл {file_name}.')
        else:
            print(f'Ошибка выполнения запроса на странице {page_num}.')
            break

        soup = bs(response_txt, 'html.parser')

        item_list_as_tag = soup.find_all(searh_item['el'], searh_item['attrs'])
        print(f"На странице {page_num} {len(item_list_as_tag)} вакансий")

        for item in item_list_as_tag:
            result['site'].append(site.split('/')[2])
            result['title'].append(
                item.find(searh_name['el'], searh_name['attrs']).getText())

            item_url_as_tag = item.find(searh_url['el'], searh_url['attrs'])
            if item_url_as_tag is not None:
                item_url = item_url_as_tag['href']
                item_url = site + item_url
#                item_url = site + item_url.split('/')[4].split('?')[0]
            else:
                item_url = None
            result['url'].append(item_url)

            result['salary'].append(None)
            result['salary_min'].append(None)
            result['salary_max'].append(None)
            result['salary_currency'].append(None)
            result['salary_payment_frequency'].append(None)

            salary_as_tag = item.find(searh_salary['el'], searh_salary['attrs'])

            if salary_as_tag is not None:
                salary = salary_as_tag.findChildren(recursive=False)[0].getText().replace('\u202f', '')
                if len(salary_as_tag) > 1: # найдем периодичность выплат
                    result['salary_payment_frequency'][num] = salary_as_tag.findChildren(recursive=False)[1]\
                        .getText().replace('\u202f', '').replace('/', '')
            else:
                salary = None
            result['salary'][num] = salary
            if salary not in [None, 'По договорённости']:
                result['salary_currency'][num] = salary.split()[-1]
                if salary.split()[0] == 'до':
                    result['salary_max'][num] = int(''.join(salary.split()[1:3]))
                elif salary.split()[0] == 'от':
                    result['salary_min'][num] = int(''.join(salary.split()[1:3]))
                elif '—' in salary.split(): # задан дипазон
                    result['salary_min'][num] = int(''.join(salary.split()[:-1][:2]))
                    result['salary_max'][num] = int(''.join(salary.split()[:-1][3:]))
                elif salary.split()[0].isdigit(): # зарплата указана одним числом
                    result['salary_min'][num] = int(''.join(salary.split()[:2]))
                    result['salary_max'][num] = int(''.join(salary.split()[:2]))

            num += 1

        if soup.find(searh_button_next['el'], searh_button_next['attrs']) is None:
            break
        else:
            url = site + soup.find(searh_button_next['el'], searh_button_next['attrs'])['href']
            print(f'Обработана страница {page_num}.')
            if page_num >= max_page_num:
                break

    # df = pd.DataFrame(result)
    # df.to_excel('sj_vacancy_result.xlsx', index=False)

with MongoClient('localhost', 27017) as client:
    db = client['vacancy']
    col_hh = db.content
    fields = list(result.keys())
    item_added = 0
    for i in range(len(result[list(result.keys())[0]])):
        doc = {fields: result[fields][i] for j, fields in enumerate(fields, 0)}
        doc_list = list(col_hh.find({'url': result['url'][i]}, {'_id': 1}))
        if len(doc_list) == 0:
            new_doc = col_hh.insert_one(doc)
            item_added += 1
        else:
            new_doc = col_hh.replace_one(doc_list[0], doc)
            pass
        print(doc)

    pass
    client.close()
print(f'Получено {num} вакансий. Добавлено {item_added} вакансий')


print('End')
