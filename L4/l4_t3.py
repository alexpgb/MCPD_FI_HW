from lxml import html
import requests
from pprint import pprint
from pymongo import MongoClient
import datetime
import pytz


def date_str_to_utc(date_str, date_time_now):
    now = date_time_now
    date_time_as_list = date_str.replace(',', '').split()  # 00:00,  2 октября 2021' удалим запятую
    date_time_as_dict = {'year': None, 'month': None, 'day': None, 'time': None}
    if 'в' in date_time_as_list:
        date_time_as_list.remove('в')
    if 'вчера' in date_time_as_list:
        now = date_time_now - datetime.timedelta(days=1)
        date_time_as_list.remove('вчера')
    # print(date_time_as_list)
    time = [i for i in date_time_as_list if ':' in i]
    if len(time) > 0:  # есть время в составе даты времени
        date_time_as_dict['time'] = time[0]
    else:  # нет времени в составе даты времени
        date_time_as_dict['time'] = '00:00'
    date_time_as_list = [i for i in date_time_as_list if ':' not in i]  # Удалим время из списка
    # print(date_time_as_list)
    year = [i for i in date_time_as_list if len(i) == 4]  # найдем год в составе даты времени
    if len(year) > 0:
        date_time_as_dict['year'] = year[0]
        date_time_as_list.remove(year[0])  # Удалим найденный год
    else:
        date_time_as_dict['year'] = str(now.year)
    month = [i for i in date_time_as_list if i in month_rus_to_num_dict.keys()]
    if len(month) > 0:  # есть месяц в родительном падеже
        date_time_as_dict['month'] = month_rus_to_num_dict[month[0]]
        #     print(date_time_as_list, month[0])
        date_time_as_list.remove(month[0])  # Удалим найденный месяц
    # у нас остались в списке 1 или 2 объекта день и месяц или 0 объектово если было только вчера и/или время
    # если 1 то это день, если 2, то день и месяц.
    if len(date_time_as_list) == 1:
        date_time_as_dict['day'] = date_time_as_list[0]
    elif len(date_time_as_list) == 2:
        date_time_as_dict['day'] = date_time_as_list[0]
        date_time_as_dict['month'] = date_time_as_list[1]
    if date_time_as_dict['day'] is None:
        date_time_as_dict['day'] = str(now.day)
    if date_time_as_dict['month'] is None:
        date_time_as_dict['month'] = str(now.month)
    result = ' '.join([date_time_as_dict['time'],
                       date_time_as_dict['day'],
                       date_time_as_dict['month'],
                       date_time_as_dict['year']])
    result = datetime.datetime.strptime(result, '%H:%M %d %m %Y')
    return result


site = 'https://yandex.ru/news/'
headers = {
    'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/93.0.4577.63 Safari/537.36'}

month_rus_to_num_dict = {
    'января': '1',
    'февраля': '2',
    'марта': '3',
    'апреля': '4',
    'мая': '5',
    'июня': '6',
    'июля': '7',
    'августа': '8',
    'сентября': '9',
    'октября': '10',
    'ноября': '11',
    'декабря': '12'
}

tz_moscow = pytz.timezone('Europe/Moscow')
result_list = []  # {site, title, url, publication_date, source_name, source_url, digest}
item_num = 0
is_break = True  # чтобы было можно выполнять запросы в режиме отладки

while True:
    response = requests.get(site, headers=headers)
    print(response.request.url)
    print(response)
    if not response.ok:
        print(f'Ошибка выполнения запроса')
        break

    dom_root = html.fromstring(response.text)

    criteria_list = []
    # основная новость
    criteria_list.append({'item_wrap': "//div[@class='mg-card__inner']",
                          'item_name': ".//h2/text()",
                          'item_url': "./a/@href",
                          'item_publication_date_UTC': "./div[contains(@class, 'mg-card-footer')]/div//span[@class='mg-card-source__time']/text()",
                          'item_source_name': "./div[contains(@class, 'mg-card-footer')]/div//a/text()",
                          'item_source_url': None,
                          'digest': "./div[@class='mg-card__annotation']/text()"})
    # Большие квадраты
    criteria_list.append({'item_wrap': "//article[contains(@class, 'mg-card_flexible-single')]",
                          'item_name': ".//div/a[@class='mg-card__link']/h2/text()",
                          'item_url': ".//div/a/@href",
                          'item_publication_date_UTC': "./div[contains(@class, 'mg-card-footer')]/div//span[@class='mg-card-source__time']/text()",
                          'item_source_name': "./div[contains(@class, 'mg-card-footer')]/div//a/text()",
                          'item_source_url': None,
                          'digest': ".//div[@class='mg-card__annotation']/text()"})
    # маленькие квадраты
    criteria_list.append({'item_wrap': "//article[contains(@class, 'mg-card_flexible-half')]",
                          'item_name': ".//div/a[@class='mg-card__link']/h2/text()",
                          'item_url': ".//div/a/@href",
                          'item_publication_date_UTC': "./div[contains(@class, 'mg-card-footer')]/div//span[@class='mg-card-source__time']/text()",
                          'item_source_name': "./div[contains(@class, 'mg-card-footer')]/div//a/text()",
                          'item_source_url': None,
                          'digest': ".//div[@class='mg-card__annotation']/text()"})

    # ну и хватит
    # criteria_list.append({'item_wrap': "",
    #                       'item_name': ".",
    #                       'item_url': ".",
    #                       'item_publication_date_UTC': ".",
    #                       'item_source_name': ".",
    #                       'item_source_url': None,
    #                       'digest': "."})

    for criteria_num, criteria in enumerate(criteria_list, 1):
        items_list = dom_root.xpath(criteria['item_wrap'])  # получили список контейнеров для критерия
        if len(items_list) > 0:
            for item in items_list:  # проходим по каждому контейнеру и достаем название и ссылку
                item_name = None
                item_url = None
                item_publication_date_UTC = None
                item_source_name = None
                item_source_url = None
                item_digest = None
                # {site, title, url}                        # и заносим в список
                item_name = ''.join(item.xpath(criteria['item_name'])).strip().replace('\xa0', ' ')
                # url нужно обработать, может быть с адресом другого сайта
                # https://moslenta.ru/news/moskvicham-rasskazali-o-vozvrashenii-solnechnoi-pogody-01-10-2021.htm?utm_source=from_lenta
                item_url = ''.join(item.xpath(criteria['item_url']))
                if item_url[0] == '/':
                    item_url = site.split('/')[2] + item_url
                elif item_url[0].upper() == 'H':
                    item_url = '/'.join(item_url.split('/')[2:])

                # на титульной странице может не быть даты публикации
                if criteria['item_publication_date_UTC'] is not None:
                    item_publication_date_UTC = ''.join(item.xpath(criteria['item_publication_date_UTC'])).strip()

                if criteria['item_source_name'] is not None:
                    item_source_name = ''.join(item.xpath(criteria['item_source_name'])).strip()

                if criteria['item_source_url'] is not None:
                    item_source_url = ''.join(item.xpath(criteria['item_source_url'])).strip()

                if criteria['digest'] is not None:
                    item_digest = ''.join(item.xpath(criteria['digest'])).replace('\xa0', ' ')

                if len(item_url) > 0:
                    result_list.append({'site': site.split('/')[2],
                                        'title': item_name,
                                        'url': item_url,
                                        'publication_date_UTC': item_publication_date_UTC,
                                        'source_name': item_source_name,
                                        'source_url': item_source_url,
                                        'digest': item_digest})
                    item_num += 1
            print(result_list[-1], criteria['item_wrap'])
            pass
        pass
        print(f'criteria_num {criteria_num}')

    print(f'Собрано {item_num} записей')
    item_num = 0
    date_time_now = datetime.datetime.now(tz_moscow)
    for el in result_list:  # обработаем полученный список
        if el['publication_date_UTC'] is not None:
            # Дата публикации может быть без времени. '30 сентября 2021'
            # Дата публикации может быть без даты '00:02'
            el['publication_date_UTC'] = date_str_to_utc(el['publication_date_UTC'], date_time_now)
            el['publication_date_UTC'] = pytz.timezone('Europe/Moscow').localize(el['publication_date_UTC'])
            el['publication_date_UTC'] = el['publication_date_UTC'].astimezone(pytz.timezone('Etc/UTC'))
            item_num += 1
        print(el)
    print(f'Обработано {item_num} записей')
    item_num = 0

    with MongoClient('localhost', 27017) as client:
        db = client['news']
        col_news = db.content
        for el in result_list:
            doc_list = list(col_news.find({'url': el['url']}, {'_id': 1}))
            if len(doc_list) == 0:
                new_doc = col_news.insert_one(el)
                print(new_doc)
                item_num += 1
            else:
                new_doc = col_news.replace_one(doc_list[0], el)
                pass
            pass

    print(f'Сохранено {item_num} записей')
    item_num = 0

    if is_break:
        break

print('End')
