import requests
# import json
from pathlib import Path
from bs4 import BeautifulSoup as bs
from pprint import pprint
# import pandas as pd
from pymongo import MongoClient

search_text = input('Введите строку поиска (слова, разделенные пробелом) :')
max_page_num = input('Укажите сколько страниц обработать:')

if len(search_text) > 0 and len(max_page_num) > 0:
    max_page_num = int(max_page_num)
    site = 'https://hh.ru'
    access_point = '/search/vacancy'
    # suffix = '.json'
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36'}
#    search_text = 'data science python'
    params = {'st': 'searchVacancy',
              'text': search_text,
              'area': [1, 4],  # Москва и Новосибирск
              'area': [3],     # Свердловская область
              'salary': None,
              'currency_code': 'RUR',
              'experience': 'doesNotMatter',
              'order_by': 'relevance',
              'search_period': 0,
              'items_on_page': 10,
              'no_magic': 'true'}

    url = site + access_point

    hh_searh_vacancy = {}
    hh_searh_vacancy_name = {}
    hh_searh_vacancy_salary = {}
    hh_searh_vacancy['el'] = 'div'
    hh_searh_vacancy['attrs'] = {'class': 'vacancy-serp-item__row vacancy-serp-item__row_header'}
    hh_searh_vacancy_name['el'] = 'a'
    hh_searh_vacancy_name['attrs'] = {'class': 'bloko-link', 'data-qa': 'vacancy-serp__vacancy-title'}
    hh_searh_vacancy_salary['el'] = 'span'
    hh_searh_vacancy_salary['attrs'] = {'class': 'bloko-header-section-3 bloko-header-section-3_lite',
                                        'data-qa': 'vacancy-serp__vacancy-compensation'}

    hh_searh_vacancy_button_next = {'el': 'a', 'attrs': {'class': 'bloko-button',
                                                         'data-qa': 'pager-next'}}
    hh_searh_vacancy_button_pressed = {'el': 'span', 'attrs': {'class': 'bloko-button bloko-button_pressed',
                                                               'data-qa': 'pager-page'}}

    # <span class="bloko-button bloko-button_pressed" to="/search/vacancy?st=searchVacancy&amp;text=data+science+python&amp;area=1&amp;area=4&amp;currency_code=RUR&amp;experience=doesNotMatter&amp;order_by=relevance&amp;search_period=0&amp;items_on_page=10&amp;no_magic=true&amp;page=1" data-qa="pager-page"><span>2</span></span>

    vacancy_result = {'title': [], 'salary': [], 'salary_min': [], 'salary_max': [], 'salary_currency': [], 'url': []}
    page_num = 0
    num = 0
    while True:
        page_num += 1
        file_name = rf'.\L2\HH_pages\hh_response_{page_num}.html'
        if 1 == 1 or not Path(file_name).exists():
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

        else:
            with open(file_name, 'rb') as f:
                response_txt = f.read()
                f.close()
                print(f'Содержимое файла {file_name} прочтено.')

        soup = bs(response_txt, 'html.parser')

        vacancy_list_as_tag = soup.find_all(hh_searh_vacancy['el'], hh_searh_vacancy['attrs'])
        print(f"В файле {file_name}, на странице {page_num} {len(vacancy_list_as_tag)} вакансий")
        #             {soup.find(hh_searh_vacancy_button_pressed['el'], hh_searh_vacancy_button_pressed['attrs']).getText()} \

        for vacancy_item in vacancy_list_as_tag:
            vacancy_result['title'].append(
                vacancy_item.find(hh_searh_vacancy_name['el'], hh_searh_vacancy_name['attrs']).getText())
            if vacancy_item.find(hh_searh_vacancy_salary['el'], hh_searh_vacancy_salary['attrs']) is None:
                salary = None
            else:
                salary = vacancy_item.find(hh_searh_vacancy_salary['el'],
                                           hh_searh_vacancy_salary['attrs']).getText().replace('\u202f', '')
            vacancy_result['salary'].append(salary)
            vacancy_result['salary_min'].append(None)
            vacancy_result['salary_max'].append(None)
            vacancy_result['salary_currency'].append(None)
            if salary is not None:
                vacancy_result['salary_currency'][num] = salary.split()[-1]
                if salary.split()[0] == 'до':
                    vacancy_result['salary_max'][num] = salary.split()[1]
                if salary.split()[0] == 'от':
                    vacancy_result['salary_min'][num] = salary.split()[1]
                if salary.split()[1] == '–':
                    vacancy_result['salary_min'][num] = salary.split()[0]
                    vacancy_result['salary_max'][num] = salary.split()[2]

            v_url = vacancy_item.find(hh_searh_vacancy_name['el'], hh_searh_vacancy_name['attrs'])['href']
            if v_url is not None:
                v_url = site + '/vacancy/' + v_url.split('/')[4].split('?')[0]
            vacancy_result['url'].append(v_url)
            num += 1

        if soup.find(hh_searh_vacancy_button_next['el'], hh_searh_vacancy_button_next['attrs']) is None:
            break
        else:
            url = site + soup.find(hh_searh_vacancy_button_next['el'], hh_searh_vacancy_button_next['attrs'])['href']
            print(f'Обработана страница {page_num}.')
            if page_num >= max_page_num:
                break

    df = pd.DataFrame(vacancy_result)
    df.to_excel('hh_vacancy_result.xlsx', index=False)


print('End')
