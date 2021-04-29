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
                time.sleep(3)
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
        if character in temp['id']:
            pass
        else:
            temp['id'].append(character)
    with open('cogs/characters_blacklist.json', 'w') as file:
        json.dump(temp, file)


mainloop(1, 10)

