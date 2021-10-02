import requests
import json

server_name = 'https://api.github.com'
gh_username = 'alexpgb'
access_point = 'users'
access_point_repos = 'repos'
url = server_name + '/' + access_point + '/' + gh_username + '/'+access_point_repos
print(url)
response = requests.get(url)

if response.ok: # 200..399
    t = [f"\n {count}. {i['name']}." for count, i in enumerate(response.json(), 1)]
    print(f'Репозитории пользователя {gh_username} :', *t)
    with open('L1_t1_repo_'+gh_username+'.json', 'w') as f:
        json.dump(response.json(), f)
        f.close()
    print(f'Файл записан')


print(response.content)