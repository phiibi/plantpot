import json
import requests
import asyncio
import time


def checkanime(id):
    d = requests.get(f'https://api.jikan.moe/v3/anime/{id}')
    d = d.json()
    if 'Rx' in d['rating']:
        return False
    return True

def mainloop(low, high):
    blacklist_character = []
    blacklist_anime = []
    whitelist = []
    for i in range(low, high):
        d = requests.get(f'https://api.jikan.moe/v3/top/characters/{i}')
        d = d.json()
        for character in d['top']:
            if not character['animeography']:
                blacklist_character.append(character['mal_id'])
            for show in character['animeography']:
                time.sleep(6)
                if whitelist.count(show['mal_id']):
                    pass
                elif blacklist_anime.count(show['mal_id']):
                    blacklist_character.append(character['mal_id'])
                    break
                elif not checkanime(show['mal_id']):
                    blacklist_anime.append(show['mal_id'])
                    blacklist_character.append(character['mal_id'])
                    print(blacklist_character)
                    break
                else:
                    whitelist.append(show['mal_id'])
    with open('cogs/characters_blacklist.json', 'r') as file:
        d = json.loads(file.read())
    temp = d
    for character in blacklist_character:
        temp['id'].append(character)
    with open('cogs/characters_blacklist.json', 'w') as file:
        json.dump(temp, file)


print(checkanime(39392))
mainloop(10, 19)
print('10, 19')
mainloop(20, 29)
print('20, 29')
mainloop(30, 39)
print('30, 39')
mainloop(40, 49)
print('40, 49')
mainloop(50, 59)
print('50, 59')
mainloop(60, 69)
print('60, 69')
mainloop(70, 79)
print('70, 79')
mainloop(80, 89)
print('80, 89')
mainloop(90, 99)
print('90, 99')
