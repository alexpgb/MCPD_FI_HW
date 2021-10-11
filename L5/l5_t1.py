# from lxml import html
# import requests
# from pprint import pprint
from pymongo import MongoClient
import datetime
import pytz
from selenium import webdriver  # импорт драйвера
from selenium.webdriver.common.keys import Keys  # Импорт модуля для ввода нажатия клавиш или комбинации клавиш
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time


def date_str_to_utc(date_str, date_time_now):
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
    now = date_time_now
    date_time_as_list = date_str.replace(',', '').split()  # 00:00,  2 октября 2021' удалим запятую
    date_time_as_dict = {'year': None, 'month': None, 'day': None, 'time': None}
    date_time_as_list = [el.lower() for el in date_time_as_list]
    if 'в' in date_time_as_list:
        date_time_as_list.remove('в')
    if 'сегодня' in date_time_as_list:
        date_time_as_list.remove('сегодня')
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


site = 'https://mail.ru/'
max_page_num = 50
# проверить как работает зависание мыши на GB
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--incognito')  # чтобы не запоминал пароль.
result_dict = {}
tz_moscow = pytz.timezone('Europe/Moscow')
result_list = []  # {mail_box, direction, correspondent, date_send, subject, body_html, url, msg_id}
mail_box = 'study.ai_172@mail.ru'
passw = 'NextPassword172???'
with MongoClient('localhost', 27017) as client:  # т.к. открытие писем происходит долго, по базе нужно проверять сразу
    db = client['email']
    col_news = db.content
    # col_news.delete_many({}) # для отладки

    with webdriver.Chrome(executable_path='./L5/chromedriver.exe', options=chrome_options) as driver:
        driver.get(site)
        login = driver.find_element_by_xpath(
            "//form[contains(@class,'body svelte')]//input[contains(@class,'email-input')]")
        login.send_keys(mail_box)
        button_enter_passw = driver.find_element_by_xpath(
            "//button[contains(@data-testid,'enter-password')]")
        button_enter_passw.send_keys(Keys.ENTER)
        # полный вызов https://russianblogs.com/article/96241598459/
        # wait_result = WebDriverWait(driver=self.driver, timeout=300, poll_frequency=0.5, ignored_exceptions=None).until(
        #     EC.text_to_be_present_in_element((By.XPATH, '// * [@ id = "VolumeTable"] / tbody / tr [1] / td [4] / label'),
        #                                      u'available '))
        field_passw_wait = WebDriverWait(driver, 10). \
            until(EC.visibility_of_element_located((By.XPATH, "//input[contains(@class,'password-input')]")))
        # здесь нужно указывать относительный адрес или абсолютный адрес элемента?
        # driver.implicitly_wait(3)
        field_passw = driver.find_element_by_xpath(
            "//input[contains(@class,'password-input')]")
        field_passw.send_keys(passw)
        button_enter_to_mail = driver.find_element_by_xpath("//button[@data-testid='login-to-mail']").click()
        # button_enter_to_mail.send_keys(Keys.ENTER)
        el_num = None
        page_num = 0
        # mail_box_title_wait = WebDriverWait(driver, 10).until(EC.title_is)
        mail_box_el_wait = WebDriverWait(driver, 10). \
            until(EC.visibility_of_element_located((By.XPATH, "//a[contains(@class,'llc')]")))
        if 'Входящие' in driver.title.split():
            print('Зашли в if')
            el_num = driver.title.split()[0][1:-1]
            if el_num.isdigit():
                int(el_num)
            while True:
                page_num += 1
                el_on_page = driver.find_elements_by_xpath("//a[contains(@class,'llc')]")
                el_on_page_dict = \
                    {el.get_attribute('data-id'): '/'.join(el.get_attribute('href').split('/')[:5]) for el in el_on_page}

                for el in list(el_on_page_dict.keys()):
                    if col_news.count_documents({'msg_id': el}) > 0:
                        del el_on_page_dict[el]
                        pass

                el_new_dict = {k: el_on_page_dict[k] for k, _ in set(el_on_page_dict.items()) - set(result_dict.items())}
                if len(el_new_dict) == 0:   # упали на дно.
                    break
                result_dict = result_dict | el_new_dict
                              
                go_bottom = ActionChains(driver).move_to_element(el_on_page[-1])
                go_bottom.perform()
                print(f'page num {page_num} el_on_page {len(el_on_page)} el_on_page {el_on_page[-1]} result_dict'
                      f' {len(result_dict)}')
                if page_num >= max_page_num:
                    break
                time.sleep(2)

            for i, item in enumerate(result_dict, 1):
                date_time_now = datetime.datetime.now(tz_moscow)
                driver.get(result_dict[item])
                # вставить задержку
                mail_open_wait = WebDriverWait(driver, 10). \
                    until(
                    EC.visibility_of_element_located((By.XPATH, "//div[@id='style_" + item.split(':')[1] + "_BODY']/div")))
                item_from = driver.find_element_by_xpath(
                    "//div[@class='letter__author']/span[@class='letter-contact']").get_attribute(
                    'title')
                item_date_send = driver.find_element_by_class_name("letter__date").text
                item_date_send = date_str_to_utc(item_date_send, date_time_now)
                item_subject = driver.find_element_by_class_name("thread__subject").text
                item_body_html = driver.find_element_by_xpath("//div[@id='style_" + item.split(':')[1] + "_BODY']/div"). \
                    get_attribute('innerHTML').replace('\n', '').replace('\t', '')
                item_body_html = '<html><body>' + item_body_html + '</body></html>'

                result_list.append({'mail_box': mail_box,
                                    'direction': 'inbound',
                                    'correspondent': item_from,
                                    'date_send': item_date_send,
                                    'subject': item_subject,
                                    'body_html': item_body_html,
                                    'url': result_dict[item],
                                    'msg_id': item})

                print(result_list[-1]['correspondent'], result_list[-1]['date_send'], result_list[-1]['subject'])
                print(f'Обработано {i}-е письмо ')
        print(f'Работа Selenium завершена получено {len(result_list)} записей.')
        driver.close()
    item_num = 0
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

print('End')
