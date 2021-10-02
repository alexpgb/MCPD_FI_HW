import requests
import json

headers = {'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36'}
access_point = 'https://api.mapbox.com/geocoding/v5/mapbox.places/'
suffix = '.json'
search_text = 'Верхняя Пышма'
geographic_coordinates = {'longitude': 60.58333, 'latitude': 56.8333}
params = {'country': 'RU', 'language': 'de'}
urls = []
response = []
urls.append(access_point + search_text + suffix)
urls.append(access_point + str(geographic_coordinates['longitude'])+','+str(geographic_coordinates['latitude']) + suffix)
print(urls)
with open('api_mapbox_token.txt') as f:
    params['access_token'] = f.readline()
    f.close()
for i, url in enumerate(urls, 0):
    if len(params['access_token']) == 0:
        break
    response.append(requests.get(url, params=params, headers=headers))
    print(url)
    print(response[i])
    if response[i].ok: # 200..399
        with open(f'L1_t2_response_{i}.json', 'w') as f:
            json.dump(response[i].json(), f)
            f.close()
        print(f'Файл записан')


