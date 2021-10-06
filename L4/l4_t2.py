from lxml import html
import requests
from pprint import pprint
from pymongo import MongoClient
import datetime
import pytz

site = 'https://lenta.ru/'
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
    criteria_list.append({'item_wrap': "//div[@class='first-item']",
                           'item_name': ".//h2//a/text()",
                           'item_url': "..//h2//a/@href",
                           'item_publication_date_UTC': ".//h2//a/time/@datetime",
                          'digest': None})
    # Основной блок новостей
    criteria_list.append({'item_wrap': "//div[@class='span4']/div[@class='item']",
                          'item_name': "./a/text()",
                          'item_url': "./a/@href",
                          'item_publication_date_UTC': "./a/time/@datetime",
                          'digest': None})                  # нет дайджеста
    # Блок Главные новости в правой колонке
    criteria_list.append({'item_wrap': "//div[@class='b-yellow-box__wrap']/div[@class='item']",
                          'item_name': "./a/text()",
                          'item_url': "./a/@href",
                          'item_publication_date_UTC': None,  # нет даты публикации
                          'digest': None})                    #
    # следующая главная новость
    criteria_list.append({'item_wrap': "//div[@class='b-feature__wrap']",
                          'item_name': ".//h1[@class='b-feature__title']/text()",
                          'item_url': ".//h1[@class='b-feature__title']/../../a/@href",
                          'item_publication_date_UTC': ".//time/text()",
                          'digest': ".//a//h2[@class='rightcol']/text()"})

    # блоки с фотками
    criteria_list.append({'item_wrap': "//div[@class='span4']/section/div[@class='item article']",
                          'item_name': ".//a[@class='titles']/h3/text()",
                          'item_url': ".//a[@class='titles']/@href",
                          'item_publication_date_UTC': ".//div//span[contains(@class,'time')]/text()",
                          'digest': ".//a/h3/../span/text()"})
    # ну и хватит
    # criteria_list.append({'item_wrap': "",
    #                       'item_name': ".",
    #                       'item_url': ".",
    #                       'item_publication_date_UTC': ".",
    #                       'digest': "."})



    for criteria_num, criteria in enumerate(criteria_list, 1):
        items_list = dom_root.xpath(criteria['item_wrap'])  # получили список контейнеров для критерия
        if len(items_list) > 0:
            for item in items_list:                         # проходим по каждому контейнеру и достаем название и ссылку
                item_name = None
                item_url = None
                item_publication_date_UTC = None
                item_source_name = None
                item_source_url = None
                item_digest = None
                # {site, title, url}                        # и заносим в список
                item_name = ''.join(item.xpath(criteria['item_name'])).replace('\xa0', ' ')
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

                item_source_name = item_url.split('/')[0]
                if criteria['digest'] is not None:
                    item_digest = ''.join(item.xpath(criteria['digest'])).replace('\xa0', ' ')

                if len(item_url) > 0:
                    result_list.append({'site': site.split('/')[2],
                                        'title': item_name,
                                        'url':  item_url,
                                        'publication_date_UTC': item_publication_date_UTC,
                                        'source_name': item_source_name,
                                        'source_url': None,
                                        'digest': None})

                print(result_list[-1], criteria['item_wrap'])
                item_num += 1
            pass
        pass
        print(f'criteria_num {criteria_num}')

    print(f'Собрано {item_num} записей')
    item_num = 0
    for el in result_list:                        # обработаем полученный список
        if el['publication_date_UTC'] is None:
            response = requests.get('https://' + el['url'], headers=headers)
            if response.ok:
                dom_root = html.fromstring(response.text)
                items_list = dom_root.xpath("//div[contains(@class, 'b-topic__header')]")  # получим списко контейнеров
                # if len(items_list) > 0:
                item = items_list[0]
                item_publication_date_UTC = ''.join(item.xpath("./div/time/text()")).strip().replace('\xa0', ' ')
                el['publication_date_UTC'] = item_publication_date_UTC

        date_time_as_list = el['publication_date_UTC'].split()
        if len(date_time_as_list) > 0:
            # Дата публикации может быть без времени. '30 сентября 2021'
            # Дата публикации может быть без даты '00:02'
            if len(date_time_as_list) == 1:  # только время
                date_time_as_list[0] = date_time_as_list[0] + ','
                date_time_as_list.extend(
                    [str(datetime.datetime.now(tz_moscow).day), str(datetime.datetime.now(tz_moscow).month),
                     str(datetime.datetime.now(tz_moscow).year)])
            elif len(date_time_as_list) == 3:  # только дата
                date_time_as_list.insert(0, '00:00, ')
            if date_time_as_list[2] in month_rus_to_num_dict.keys():
                date_time_as_list[2] = month_rus_to_num_dict[date_time_as_list[2]]
            el['publication_date_UTC'] = ' '.join(date_time_as_list)
            el['publication_date_UTC'] = datetime.datetime.strptime(el['publication_date_UTC'], '%H:%M, %d %m %Y')
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
