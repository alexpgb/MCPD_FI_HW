from lxml import html
import requests
from pprint import pprint
from pymongo import MongoClient
import datetime
import pytz

site = 'https://news.mail.ru/'
headers = {
    'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/93.0.4577.63 Safari/537.36'}

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

    # Соберем главные новости со страницы
    # Сделаем список с критериями
# блок с основными новостями
# //div[contains(@class, 'daynews__item')] - более универсальный вариант
# //div[contains(@class, 'daynews__item')]//a[@href]  # ссылка на новость
# //div[contains(@class, 'daynews__item')]//span[@class='photo__captions']/span[1][text()] - название

# остальные новости кратко
# //div[contains(@class,'cols__column')] - 4 контейнера
# //div[contains(@class, 'newsitem')]//a[contains(@class, 'newsitem__title')]  главная новость в контейнере
# //div[contains(@class, 'newsitem')]//a[contains(@class, 'newsitem__title')]/@href - ссылка
# //div[contains(@class, 'newsitem')]//a[contains(@class, 'newsitem__title')]/span[contains(@class, 'newsitem__title')]/text()
# //div[contains(@class,'cols__column')]//ul/li[@class='list__item'] -  остальные новости
# //ul/li[@class='list__item']//a[contains(@class, 'link_flex')]/span[@class='link__text']/text()
# //ul/li[@class='list__item']//a[contains(@class, 'link_flex')]/@href

# //div[contains(@class, 'article js-article')] блок с новостью
# //div[contains(@class, 'article js-article')]//span[contains(@class, 'note__text') and contains(@class, 'js-ago')]/text() # время назад
# //div[contains(@class, 'article js-article')]//a[contains(@class, 'link')]/@href источник - ссылка
# //div[contains(@class, 'article js-article')]//a[contains(@class, 'link')]/span[contains(@class, 'link__text')]/text() # источник текст
# //div[contains(@class, 'article js-article')]//div[contains(@class, 'article__intro')]/p/text() - дайджест новости
#
    criteria_list = []
    criteria_list.append({'item_wrap': "//div[contains(@class, 'daynews__item')]",
                           'item_name': ".//span[@class='photo__captions']/span[1]/text()",
                           'item_url': ".//a/@href"})
    # новости под топом
    criteria_list.append({'item_wrap': "//ul[@data-module='TrackBlocks']/li[@class='list__item']",
                          'item_name': ".//a/text()",
                          'item_url': ".//a/@href"})
    criteria_list.append({'item_wrap': "//div[contains(@class, 'newsitem')]//a[contains(@class, 'newsitem__title')]",
                          'item_name': "./span[contains(@class, 'newsitem__title')]/text()",
                          'item_url': "./@href"})
    criteria_list.append({'item_wrap': "//ul[contains(@class, 'list_overflow') and contains(@class, 'list')]//li[@class='list__item']",
                          'item_name': ".//a[contains(@class, 'link_flex')]/span[@class='link__text']/text()",
                          'item_url': ".//a[contains(@class, 'link_flex')]/@href"})

    for criteria_num, criteria in enumerate(criteria_list, 1):
        items_list = dom_root.xpath(criteria['item_wrap'])  # получили список контейнеров для критерия
        if len(items_list) > 0:
            for item in items_list:                         # проходим по каждому контейнеру и достаем название и ссылку
                # {site, title, url}                        # и заносим в список
                item_name = ''.join(item.xpath(criteria['item_name'])).replace('\xa0', ' ')
                item_url = ''.join(item.xpath(criteria['item_url']))
                if len(item_url) > 0:
                    result_list.append({'site': site.split('/')[2],
                                        'title': item_name,
                                        'url': item_url})
                print(result_list[-1], criteria['item_wrap'])
                item_num += 1
            pass
        pass
        print(f'criteria_num {criteria_num}')

    print(f'Собрано {item_num} записей')
    item_num = 0
    for el in result_list:                        # обработаем полученный список
        response = requests.get(el['url'], headers=headers)
        if response.ok:
            dom_root = html.fromstring(response.text)
            items_list = dom_root.xpath("//div[contains(@class, 'article js-article')]")  # получим списко контейнеров
            if len(items_list) > 0:
                item = items_list[0]
                # {publication_date_UTC, source_name, source_url, digest}
                # //div[contains(@class, 'article js-article')]//span[contains(@class, 'note__text') and contains(@class, 'js-ago')]/text() # время назад
                # //div[contains(@class, 'article js-article')] источник - ссылка
                # //div[contains(@class, 'article js-article')] # источник текст
                # //div[contains(@class, 'article js-article')]//div[contains(@class, 'article__intro')]/p/text() - дайджест новости
                item_publication_date_UTC = ''.join(item.xpath(".//span[contains(@class, 'note__text') and contains(@class, 'js-ago')]/text()")).replace('\xa0', ' ').split()[0].split(':')
                item_publication_date_UTC = (datetime.datetime.now(tz_moscow) -
                                             datetime.timedelta(hours=int(item_publication_date_UTC[0]),
                                                             minutes=int(item_publication_date_UTC[1])))

                item_source_name = ''.join(item.xpath(".//a[contains(@class, 'link')]/span[contains(@class, 'link__text')]/text()")).replace('\xa0', ' ')
                item_source_url = ''.join(item.xpath(".//a[contains(@class, 'link')]/@href"))
                item_digest = ''.join(item.xpath(".//div[contains(@class, 'article__intro')]/p/text()")).replace('\xa0', ' ')
                el['publication_date_UTC'] = item_publication_date_UTC
                el['source_name'] = item_source_name
                el['source_url'] = item_source_url
                el['digest'] = item_digest
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
