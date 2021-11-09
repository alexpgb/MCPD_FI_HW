# 1) Написать приложение, которое будет проходиться по указанному списку двух и/или более пользователей и собирать данные об их подписчиках и подписках.
# 2) По каждому пользователю, который является подписчиком или на которого подписан исследуемый объект нужно извлечь имя, id, фото (остальные данные по
# желанию). Фото можно дополнительно скачать.
# 4) Собранные данные необходимо сложить в базу данных. Структуру данных нужно заранее продумать, чтобы:
# 5) Написать запрос к базе, который вернет список подписчиков только указанного пользователя
# 6) Написать запрос к базе, который вернет список профилей, на кого подписан указанный пользователь
import scrapy
import re
import json
from urllib.parse import \
    urlencode  # принимает словарь, возвращает строку с параметрами для подстановки в ссылку запроса
from copy import deepcopy
from scrapy.http import HtmlResponse
from scrapy.http import FormRequest
from scrapy.http import Request
from instascraper.items import InstascraperItem


def get_login_info():
    info = None
    with open('.\..\..\L8\inst_login_info1.txt', 'r') as f:
        login = f.readline().strip()
        passw = f.readline().strip()
        f.close()
        # print(info)
    return dict(username=login, enc_password=passw)


class InstaSpider1Spider(scrapy.Spider):
    name = 'insta_spider1'
    allowed_domains = ['instagram.com']
    start_urls = ['http://instagram.com/']
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    user_for_parse = ['rimeks', 'pokazuema', 'ov_alexander']
    graphql_url = 'https://www.instagram.com/graphql/query/?'
    graphql_post_hash = '8c2a529969ee035a5063f2fc8602a0fd'
    api_url = 'https://i.instagram.com/api/v1/'

    # нам
    # def start_requests(self):
    #     print()
    #     for url in self.start_urls:
    #         yield Request(url, dont_filter=True)

    def parse(self, response: HtmlResponse):
        login_info = get_login_info()
        print(login_info)
        cookie = [i.decode("utf-8") for i in response.headers.getlist('Set-Cookie') if 'csrftoken' in i.decode("utf-8")]
        if len(cookie) > 0:
            csrftoken = [i for i in cookie[0].split(';') if 'csrftoken' in i][0].split('=')[1]
            print(f'csrftoken: {csrftoken}')
            yield scrapy.FormRequest(
                self.login_url,
                method='POST',
                callback=self.inst_login,
                formdata={'username': login_info['username'],
                          'enc_password': login_info['enc_password']},
                # c куками здесь не работает.
                # cookies={'csrftoken': csrftoken},
                headers={'x-csrftoken': csrftoken}
            )
            # так не работает должен быть элемент на форме
            # yield FormRequest.from_response(
            #     response.replace(url=self.login_url),
            #     method='POST',
            #     callback=self.inst_login,
            #     formdata={'username': self.login,
            #               'enc_password': self.pwd},
            #     headers={'x-csrftoken': csrftoken}
            # )
            # логин в той же сессии. Сначала работало потом перестало
            # yield response.replace(body=urlencode(login_info)).follow(self.login_url,
            #                                                method='POST',
            #                                                headers={'x-csrftoken': csrftoken},
            #                                                callback=self.inst_login)
            # так не работает!
            # 1. Как тестировать методы scrapy в дебагаере? к сожалению они возвращают результат только в Callback
            # 2. как правильно сформировать тело запроса в методе responce.follow ?
            # yield response.follow('https://www.instagram.com/accounts/login/ajax/',
            #                       method='POST',
            #                       body='{"username": "Onliskill_udm",'
            #                            ' "enc_password": "#PWD_INSTAGRAM_BROWSER:10:1635222531:ARNQAODdIXbnkU28ZzR8dqww5jp6Nk2ZaZrbqy90+3Qpec5Rf8hMzOQKE3pScLK2Mr3JL01opup5xeJw8rzqZgdfkwz/RTXED9hFOm+AEqnoety0TjFpEmZeSYGeyZ6fukv8onVRX12ewTzpDkuC"}',
            #                       cookies={'csrftoken': csrftoken},
            #                       callback=self.inst_login)

    def inst_login(self, response: HtmlResponse):
        # после регистрации переход в профиль целевого пользователя
        print(response.request.body)
        # в этом случае на вызов нашего метода возвращается json
        j_data = response.json()
        if j_data['authenticated']:
            # не очень технично, но username можно выдрать из response.url
            for user in self.user_for_parse:
                yield response.follow(
                    f'/{user}',
                    callback=self.user_parse,
                    cb_kwargs={'username': user}
                )

    def user_parse(self, response: HtmlResponse, username):
        # после перехода в профиль целевого пользователя вызываем метод подгружающий посты пользователя или подписки пользователя
        # в этом случае на вызов нашего метода возвращается html
        # попробовать  user-agent Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.85 Mobile Safari/537.36
        print(response.request.body)
        # Внимание! эта штука не работает, если у user нет ни одного поста!
        # user_id = self.fetch_user_id(response.text, username)
        # Поэтому сделаем ход конем. Откуда то же берутся данные для отображения на первой странице.
        data_j = json.loads(response.xpath('//script[@type="text/javascript" and contains(text(),"window._sharedData") '
                                           'and contains(text(),"config")]/text()').
                            get().replace('window._sharedData =', '').strip()[:-1])
        user_id = data_j.get('entry_data').get('ProfilePage')[0].get('graphql').get('user').get('id')
        # Публикации
        # jdata.get('entry_data').get('ProfilePage')[0].get('graphql').get('user').get('edge_media_collections')
        # {'count': 0, 'page_info': {'has_next_page': False, 'end_cursor': None}, 'edges': []}
        # Подписчики. Есть же профили у которых нет  подписчиков. Как понять, что туда не нужно ходить?
        followers_num = data_j.get('entry_data').get('ProfilePage')[0].get('graphql').get('user')\
            .get('edge_followed_by').get('count')
        # Подписки. Есть профили у которых нед подписок.
        follow_num = data_j.get('entry_data').get('ProfilePage')[0].get('graphql').get('user')\
            .get('edge_follow').get('count')
        # количество постов
        posts_num = data_j.get('entry_data').get('ProfilePage')[0].get('graphql').get('user').\
            get('edge_owner_to_timeline_media').get('count')
        user_info = data_j.get('entry_data').get('ProfilePage')[0].get('graphql').get('user')
        # важно понимать закрытй ли аккаунт, пока пропустим. Можно определять в подписках, но это тоже позже.
        # 'full_name': data_j.get('entry_data').get('ProfilePage')[0].get('graphql').get('user').get('full_name'),
        # 'description': data_j.get('entry_data').get('ProfilePage')[0].get('graphql').get('user').get('biography')}
        # там же page_info на первую страницу и собственно json c первой страницей публикаций
        # data_j.get('entry_data').get('ProfilePage')[0].get('graphql').get('user').get('edge_owner_to_timeline_media').get('page_info')
        # так же id и еще кучу информации о пользователе можно вытащить из результатов запроса https://www.instagram.com/{Cusername}/?__a=1
        if followers_num > 0 and 1 == 1: # если есть подписчики идем собирать подписчиков
            variables_for_followers = {'count': 12, 'search_surface': 'follow_list_page'}
            url_followers = f'{self.api_url}friendships/{user_id}/followers/?{urlencode(variables_for_followers)}'
            print()
            yield response.follow(url_followers, callback=self.user_followers_parse,
                                  headers={'user-agent': 'Instagram 155.0.0.37.107'},
                                  cb_kwargs={'username': username,
                                             'user_id': user_id,
                                             'user_info': user_info,
                                             'variables': deepcopy(variables_for_followers)},
                                  errback=self.user_parse_err)
        if follow_num > 0 and 1 == 1: # если есть подписки
            # вызов первой страницы
            # https://i.instagram.com/api/v1/friendships/1258196609/following/?count=12 - реальная ссылка
            # https://i.instagram.com/api/v1/friendships/48839790332/following/?count=12 - сформированная ссылка
            variables_for_follow = {'count': 12}
            url_follow = f'{self.api_url}friendships/{user_id}/following/?{urlencode(variables_for_follow)}'
            print(f'yield url_follow {url_follow}')
            yield response.follow(url_follow, callback=self.user_following_parse,
                                  headers={'user-agent': 'Instagram 155.0.0.37.107'},
                                  cb_kwargs={'username': username,
                                             'user_id': user_id,
                                             'user_info': user_info,
                                             'variables': deepcopy(variables_for_follow)},
                                  errback=self.user_parse_err)

        if posts_num > 0 and 1 == 0 : # если есть посты # задачи собирать посты нет.
            variables = {'id': user_id, 'first': 12}
            url_posts = f'{self.graphql_url}query_hash={self.graphql_post_hash}&{urlencode(variables)}'
            yield response.follow(url_posts, callback=self.user_post_parse,
                                  cb_kwargs={'username': username,
                                             'user_id': user_id,
                                             'variables': deepcopy(variables)},
                                  errback=self.user_parse_err)
        print()

    def user_followers_parse(self, response: HtmlResponse, username, user_id, user_info, variables):
        # здесь нужно проверить куда мы пришли, т.к. если ссылка на будет правильной, то нас забросят опять на страницу пользователя
        # подписчики
        data_j = response.json()
        # получим курсор, который покажен нам куда нужно сместитья в следующем запросе.
        # если достигли последней страницы в json будет отсутствовать поле 'next_max_id' ?
        max_id = data_j.get('next_max_id')
        if max_id is not None:
            # если есть следующая страница делаем еще один запрос
            variables['max_id'] = max_id
            # https://i.instagram.com/api/v1/friendships/<userid>/followers/?count=12&max_id=12&search_surface=follow_list_page
            url = f'{response.request.url.split("?")[0]}?{urlencode(variables)}'
            yield response.follow(url, callback=self.user_followers_parse,
                                  headers={'user-agent': 'Instagram 155.0.0.37.107'},
                                  cb_kwargs={'username': username,
                                             'user_id': user_id,
                                             'user_info': user_info,
                                             'variables': deepcopy(variables)},
                                  errback=self.user_parse_err)
        followers = data_j.get('users')
        for follower in followers:
            item = InstascraperItem(
                friend_type='follower',
                user_id=user_id,
                user_name=username,
                user_data=user_info,
                friend_id=follower.get('pk'),
                friend_name=follower.get('username'),
                friend_data=follower)
            yield item
        print()

    def user_following_parse(self, response: HtmlResponse, username, user_id, user_info, variables):
        # здесь нужно проверить куда мы пришли, т.к. если ссылка на будет правильной, то нас забросят опять на страницу пользователя
        # подписки
        data_j = response.json()
        # получим курсор, который покажен нам куда нужно сместитья в следующем запросе.
        # если достигли последней страницы в json будет отсутствовать поле 'next_max_id'?
        max_id = data_j.get('next_max_id')
        if max_id is not None:
            # если есть следующая страница делаем еще один запрос
            variables['max_id'] = max_id
            # https://i.instagram.com/api/v1/friendships/<userid>/followers/?count=12&max_id=12&search_surface=follow_list_page
            url = f'{response.request.url.split("?")[0]}?{urlencode(variables)}'
            yield response.follow(url, callback=self.user_following_parse,
                                  headers={'user-agent': 'Instagram 155.0.0.37.107'},
                                  cb_kwargs={'username': username,
                                             'user_id': user_id,
                                             'user_info': user_info,
                                             'variables': deepcopy(variables)},
                                  errback=self.user_parse_err)
        following_list = data_j.get('users')
        for following in following_list:
            item = InstascraperItem(
                friend_type='following',
                user_id=user_id,
                user_name=username,
                user_data=user_info,
                friend_id=following.get('pk'),
                friend_name=following.get('username'),
                friend_data=following)
            yield item
        print()

    def user_post_parse(self, response: HtmlResponse, username, user_id, user_info, variables):
        # здесь на вызов метода возвращается json поэтому его можно парсить через json.
        data_j = response.json()
        page_info = data_j.get('data').get('user').get('edge_owner_to_timeline_media').get('page_info')
        if page_info.get('has_next_page'):
            variables['after'] = page_info.get('end_cursor')
            url_posts = f'{self.graphql_url}query_hash={self.graphql_post_hash}&{urlencode(variables)}'
            yield response.follow(url_posts, callback=self.user_post_parse,
                                  cb_kwargs={'username': username,
                                             'user_id': user_id,
                                             'variables': deepcopy(variables)})
        posts = data_j.get('data').get('user').get('edge_owner_to_timeline_media').get('edges')
        # здесь этот item не будет работать. По хорошему нужно отдельный паук на сбор информации о пользователе, который
        # работает просле прохода паука работающего на сбор информации о френдах.
        for post in posts:
            item = InstascraperItem(
                user_id=user_id,
                user_name=username,
                photo=post.get('node').get('display_url'),
                likes=post.get('node').get('edge_media_preview_like').get('count'),
                post_data=post.get('node')
            )
            yield item
            print()

    def user_parse_err(self, response: HtmlResponse, username, user_id, user_info, variables):
        print(f'ошибка. username: {username} url: {response.request.url} variables: {variables}')
        pass

    # def fetch_user_id(self, text, username):
    #     matched = re.search('{\"id\":\"\\d+\",\"username\":\"%s\"}' %username, text)
    #     if matched is not None:
    #         matched = matched.group()
    #     return json.loads(matched).get('id')
