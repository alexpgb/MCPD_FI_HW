import requests
import json
# from pathlib import Path
from bs4 import BeautifulSoup as bs
from pprint import pprint
import pandas as pd

"""
Наша цель объекты типа Item мы хотим получить доступ к их свойствам и сохранить их в файл.
Соберм список объектов типа Item потом сохраним свойства каждого объекта Item в файл.
Есть вспомогательные объект сайт Site
В иерархической модели объекты типа Item размещаются внутри объектов типа Folder.
Item такие же как фолдер по сути нечем не отличаются, в них могут быть вложены другоие объеты,
только это тот минимальный уровень детализиции, который мы ищем в этой задаче (у них другой критерий поиска на стр).
Есть объект скрапер, который принимает объект сайт, и корневой объект Folder.
Задача скрапера пройти по всем страницам сайта и сложить в объект Folder
Создает начальный обект Page, который
возвращает список объектов типа Folder и Item. Если у объекта Page есть следующая страница, переходи на нее и повторяет
то же самое пока не обойдет все страницы объекта Folder.
Объект скрапер инициализирует объект Folder
Для наполнения объекта Folder вложенными объектами используется объект Page. 
Сначала инициализируем объект типа Folder являющийся корнем. Передадим ему ссылку на его содержимое.
Для достпуа к вложенным объектам Объекты типа Page 
Объект Page делает запрос и инициализирует объекты типа Folder, Item 

"""
headers = {
    'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/93.0.4577.63 Safari/537.36'}


class Site:
    def __init__(self, url):
        self.url = url


class Scraper:
    def __init__(self, site, folder, headers):
        self.site = site  # объект типа site
        self.headers = headers  # заголовки
        self.processed_folder = folder  # обрабатываемый обект Folder
        # self.result_folder_list = None  # итоговый список объектов типа item
        # self.result_item_list = None  # итоговый список объектов типа item
        self.pages_processed_num = 0  # счетчик обработанных страниц
        self.max_page_num = None  # максимальное количество просканированных страниц сайта
        self.inital_scrap_path = site.url + self.processed_folder.url  # каталог с которого начинается обработка
        self.path = None  # текущий обрабатываемый каталог
        self.recursive = False
        self.nesting_level = None
        self.status = 'Stop'
        self.search_button_next_page = {'el': 'a', 'attrs': {'class': 'page-num page-item last AJAX_toggle'}}
        self.search_folder_criteria_list = {'el': 'div', 'attrs': {
        'class': 'grid-padding grid-column-3 grid-column-large-6 grid-flex-mobile grid-column-middle-6 '
                 'grid-column-small-12 grid-left'}}
        # self.search_folder_criteria_list = {'el': 'div', 'attrs':
        #     {'class': lambda x: x and set(['grid-padding', 'grid-left', 'grid-column-large-6', 'grid-column-small-12']).
        #         issubset(x.split())}}
        self.search_folder_url_criteria_list = {'el': 'a', 'attrs': {'class': 'catalog__category-item '
                                                                              'util-hover-shadow'}}
        self.search_item_criteria_list = {'el': 'div', 'attrs':
            {'class': 'wrap-product-catalog__item grid-padding grid-column-4 '
                      'grid-column-large-6 grid-column-middle-12 grid-column-small-12 '
                      'grid-left js-product__item'}}
        self.search_item_url_criteria_list = {'el': 'a', 'attrs':
            {'class': 'block-product-catalog__item js-activate-rate util-hover-shadow clear'}}

    def start(self, result_folder_list, result_item_list, max_page_num=None, recursive=False, nesting_level=None):  # scraper
        # self.result_folder_list = []
        # self.result_item_list = []
        self.recursive = recursive
        self.nesting_level = nesting_level
        self.max_page_num = max_page_num
        self.status = 'Work'
        page = Page(self.inital_scrap_path)
        page.set_criteria(self.search_folder_criteria_list, self.search_folder_url_criteria_list,
                          self.search_item_criteria_list, self.search_item_url_criteria_list,
                          self.search_button_next_page)
        while True:
            page.get_content(self.headers)
            # не провреям на код т.к. проверка внутри page
            self.pages_processed_num += 1
            # достаем объекты типа Folder и Item
            # при доставании обектов проверяем на одинаковость линков дубликаты отбрасываем
            for f1 in page.result_folder_list:
                for f2 in result_folder_list:
                    if f1.url == f2.url:
                        f1.unique = False
                        break
                f1.parent_folder = self.processed_folder
            result_folder_list.extend(page.result_folder_list)
            self.processed_folder.child_folder_list.extend(page.result_folder_list)

            for i1 in page.result_item_list:
                for i2 in result_item_list:
                    if i1.url == i2.url:
                        i1.unique = False
                        break
                i1.parent_folder = self.processed_folder
            result_item_list.extend(page.result_item_list)
            self.processed_folder.child_item_list.extend(page.result_item_list)

            if page.next_page_exists:
                page.next_page(self.site)
            else:
                break
            if self.max_page_num is not None and self.pages_processed_num >= self.max_page_num:
                break
            pass
        # закончили сбор Folder & Item из обрабатываемого объекта Folder
        if self.recursive and (self.nesting_level is None or self.nesting_level > 1):
            # для каждого нового уникального объекта типа Folder достанем линк и передадим в scraper
            # при доставании обектов проверяем на одинаковость линков дубликаты отбрасываем
            # перед вызовом сл.скрапера проверяем счетчик вложенности при вызове следующего скрапера уменьшаем счетчик
            # вложенности на 1
            for f in self.processed_folder.child_folder_list:
                if self.max_page_num is not None and self.pages_processed_num >= self.max_page_num:
                    break
                if f.unique:
                    scraper = Scraper(self.site, f, headers=self.headers)
                    scraper.start(result_folder_list, result_item_list,
                                  max_page_num=self.max_page_num if self.max_page_num is None else
                                  self.max_page_num - self.pages_processed_num,
                                  recursive=self.recursive,
                                  nesting_level=self.nesting_level - 1 if self.nesting_level is not None else
                                  self.nesting_level)
                    self.pages_processed_num = self.pages_processed_num + scraper.pages_processed_num
                    # for f1 in scraper.result_folder_list:
                    #     for f2 in self.result_folder_list:
                    #         if f1.url == f2.url: f1.unique = False
                    #self.result_folder_list.extend(scraper.result_folder_list)

                    # for i1 in scraper.result_item_list:
                    #     for i2 in self.result_item_list:
                    #         if i1.url == i2.url: i1.unique = False
                    # self.result_item_list.extend(scraper.result_item_list)
                pass
            pass
        self.status = 'Stop'


class Page:
    """
    моделирует страницу, на которой расположены объекты Folder, Item
    """

    def __init__(self, url):
        self.url = url
        self.result_folder_list = None
        self.result_item_list = None
        self.search_folder_criteria_list = None  # критерий поиска объектов Folder
        self.search_folder_url_criteria_list = None  # критерий поиска URl объекта Folder
        self.search_next_page_criteria = None  # критерий поиска следующей страницы
        self.search_item_criteria_list = None  # критерий поиска объектов Item
        self.search_item_url_criteria_list = None
        self.request_result_code = None  # код запроса
        self.request_url = None  # запрашиваемый url из объекта request
        self.next_page_exists = False  # признак наличия сл.страницы
        self.next_page_url = None  # link на следующую страницу
        self.soup = None  #

    def set_criteria(self, search_folder_criteria_list,  # Page
                     search_folder_url_criteria_list,
                     search_item_criteria_list=None,
                     search_item_url_criteria_list=None,
                     search_next_page_criteria=None):
        self.search_folder_criteria_list = search_folder_criteria_list
        self.search_folder_url_criteria_list = search_folder_url_criteria_list
        self.search_item_criteria_list = search_item_criteria_list
        self.search_item_url_criteria_list = search_item_url_criteria_list
        self.search_next_page_criteria = search_next_page_criteria

    def get_content(self, headers):  # Page
        self.result_folder_list = []
        self.result_item_list = []
        response = requests.get(self.url, headers=headers)
        self.request_url = response.request.url
        self.request_result_code = response
        print(self.request_url)
        print(self.request_result_code)
        if response.ok:  # 200..399
            response_txt = response.content
            self.soup = bs(response_txt, 'html.parser')
            folder_list_as_tag = self.soup.find_all(self.search_folder_criteria_list['el'],
                                                    self.search_folder_criteria_list['attrs'])
            for folder_as_tag in folder_list_as_tag:
                folder = Folder(folder_as_tag, folder_as_tag.find(self.search_folder_url_criteria_list['el'],
                                                                  self.search_folder_url_criteria_list['attrs'])['href'])
                self.result_folder_list.append(folder)
            print(f'добавлено {len(folder_list_as_tag)}  Folder')

            item_list_as_tag = self.soup.find_all(self.search_item_criteria_list['el'],
                                                  self.search_item_criteria_list['attrs'])
            for item_as_tag in item_list_as_tag:
                item = Item(item_as_tag, item_as_tag.find(self.search_item_url_criteria_list['el'],
                                                          self.search_item_url_criteria_list['attrs'])['href'])
                self.result_item_list.append(item)
            print(f'добавлено {len(item_list_as_tag)}  Item')

            self.next_page_exists = False
            if self.search_next_page_criteria is not None:
                self.next_page_url = self.soup.find(self.search_next_page_criteria['el'],
                                                        self.search_next_page_criteria['attrs'])
                if self.next_page_url is not None and len(self.next_page_url) > 0:
                    self.next_page_url = self.next_page_url['href']
                    self.next_page_exists = True
        else:
            print(f'Ошибка выполнения запроса.')
        pass

    def next_page(self, site):
        self.url = site.url + self.next_page_url


class Custom_property:
    def __init__(self, property_search_expression):
        self.property_search_expression = property_search_expression  # словарь для поиска в теге
        self.value = None  # значение


class Folder:
    """
    Моделирует узел иерархической структуры сайта.
    """

    def __init__(self, soup, url):
        self.soup = soup
        self.url = url
        self.parent_folder = None
        self.unique = True
        self.name = Custom_property({'el': 'div', 'attrs': {'class': 'catalog__category-name'}})
        self.img = Custom_property({'el': 'img', 'attrs': {'class': 'grid-flex-mobile'}})
        self.category_item_tested_count = Custom_property({'el': 'span', 'attrs':
            {'class': 'catalog__category-tested'}})
        self.child_folder_list = []
        self.child_item_list = []


class Item:
    def __init__(self, soup, url):
        self.soup = soup
        self.url = url
        self.parent_folder = None
        self.unique = True
        self.name = Custom_property({'el': 'div', 'attrs': {'class': 'product__item-link'}})
        self.rating_overall = Custom_property({'el': 'div', 'attrs': {'class': ['rate', 'rating-value']}})
        self.rating_criterion_block = Custom_property({'el': 'div', 'attrs': {'class': 'rating-block'}})


search_item_rating_overall = {'el': 'div', 'attrs': {'class': ['rate', 'rating-value']}}
search_item_rating_criterion_block = {'el': 'div', 'attrs': {'class': 'rating-block'}}
search_item_rating_criterion = {'el': 'div', 'attrs': {'class': 'row'}}
search_item_rating_detail_item_name = {'el': 'div', 'attrs': {'class': 'text'}}
search_item_rating_detail_item_value = {'el': 'div', 'attrs': {'class': 'right'}}
search_item_button_next_page = {'el': 'a', 'attrs': {'class': 'page-num page-item last AJAX_toggle'}}

item_criterion_dict = {'Качество стирки хлопка': 'Quality_of_cotton_washing',
                       # Удалять   getText().replace('\u202f', '')
                       'Возможности и удобство': 'Features_and_convenience',
                       'Акустический комфорт': 'Acoustic_comfort',
                       'Эффективность отжима': 'Spin_efficiency',
                       'Качество отжима': 'Spin_quality',
                       'Эффективность нагрева': 'Heating_efficiency',
                       'Экономичность': 'Cost-effectiveness',
                       'Защита от ожога': 'Burn_protection',
                       'Удобство и шум': 'Convenience_and_noise',
                       'Эффективность уборки': 'Cleaning_efficiency',
                       'Удобство': 'Convenience',
                       'Оснащение': 'Equipment',
                       'Эффективность нагрева (СВЧ)': 'Heating_efficiency_microwave',
                       'Безопасность (СВЧ)': 'Safety_microwave',
                       'Конструкция и возможности': 'Design_and_features',
                       'Удобство чистки': 'Convenience_of_cleaning',
                       'Конструкция': 'Construction',
                       'Функциональность': 'Functionality',
                       'Изготовление': 'Production',
                       'Вкус еды': 'The_taste_of_food',
                       'Шумность': 'Noise_level',
                       'Эффективность': 'Effectiveness',
                       'Качество мытья посуды': 'The_quality_of_washing_dishes',
                       'Качество сушки': 'Drying_quality',
                       'Безопасность': 'Safety',
                       'Скорость приготовления эспрессо': 'The_speed_of_espresso_preparation',
                       'Качество эспрессо': 'Espresso_quality',
                       'Возможности': 'Features'}

item_criterion_no_dict = []

scraping_result = {'cat_name': [], 'item_tested_count': [], 'item_name': [], 'item_rating_overall': [],
                   'item_rating_detail': [], 'item_link': []}
result_folder_list = []
result_item_list = []
site = Site('https://roscontrol.com')
f_start = Folder(None, '/category/bitovaya_tehnika')
scraper = Scraper(site, f_start, headers=headers)
scraper.start(result_folder_list, result_item_list, recursive=True) # max_page_num=10, nesting_level=2,
print(f'получено {len(result_folder_list)} объктов Folder')
print(f'получено {len(result_item_list)} объектов Item')
for f in result_folder_list:
    f.name.value = f.soup.find(f.name.property_search_expression['el'],
                               f.name.property_search_expression['attrs']).getText().strip()
    f.category_item_tested_count.value = f.soup.find(f.category_item_tested_count.property_search_expression['el'],
                                                     f.category_item_tested_count.property_search_expression[
                                                         'attrs']).getText()

for i in result_item_list:
    item_rating_detail = {}
    i.name.value = i.soup.find(i.name.property_search_expression['el'],
                               i.name.property_search_expression['attrs']).getText()
    i.rating_overall.value = i.soup.find(
        i.rating_overall.property_search_expression['el'],
        i.rating_overall.property_search_expression['attrs'])
    if i.rating_overall.value is not None:
        i.rating_overall.value = i.rating_overall.value.getText().replace(' ', '')
        item_rating_criterion_block = i.soup.find(search_item_rating_criterion_block['el'],
                                                  search_item_rating_criterion_block['attrs'])
        item_rating_criterion_as_tag = item_rating_criterion_block.find_all(search_item_rating_criterion['el'],
                                                       search_item_rating_criterion['attrs'])
        for item_rating_criterion in item_rating_criterion_as_tag:
            item_rating_criterion_name = item_rating_criterion.find(
                search_item_rating_detail_item_name['el'],
                search_item_rating_detail_item_name['attrs']).getText().replace('\u202f', '')
            item_rating_criterion_value = item_rating_criterion.find(
                search_item_rating_detail_item_value['el'],
                search_item_rating_detail_item_value['attrs']).getText().replace(' ', '')
            if item_rating_criterion_name in item_criterion_dict:
                item_rating_detail[item_criterion_dict[item_rating_criterion_name]] = \
                    item_rating_criterion_value
            else:
                if item_rating_criterion_name not in item_criterion_no_dict:
                    item_rating_detail[item_rating_criterion_name] = \
                        item_rating_criterion_value
                    item_criterion_no_dict.append(item_rating_criterion_name)

    scraping_result['cat_name'].append(i.parent_folder.name.value)
    scraping_result['item_tested_count'].append(i.parent_folder.category_item_tested_count.value)
    scraping_result['item_name'].append(i.name.value)
    scraping_result['item_rating_overall'].append(i.rating_overall.value)
    scraping_result['item_link'].append(site.url + i.url)
    scraping_result['item_rating_detail'].append(item_rating_detail)

print(item_criterion_no_dict)
with open('l2_t2_result.txt', 'w') as f:
    json.dump(scraping_result, f)
    f.close()

df = pd.DataFrame(scraping_result)
df.to_excel('rc_scraping_result.xlsx', index=False)

print('End')
