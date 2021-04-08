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
                    print('safe')
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
    temp = d['ids']
    for id in blacklist_character:
        temp.append(id)
    with open('cogs/characters_blacklist.json', 'w') as file:
        json.dump(temp, file)


print(checkanime(39392))
mainloop(0, 9)
f = open("progress.txt", "a+")
f.write('0,9')
f.close()
mainloop(10, 19)
f = open("progress.txt", "a+")
f.write('10,19')
f.close()
mainloop(20, 29)
f = open("progress.txt", "a+")
f.write('20,29')
f.close()
mainloop(30, 39)
f = open("progress.txt", "a+")
f.write('40,49')
f.close()
mainloop(50, 59)
f = open("progress.txt", "a+")
f.write('60,69')
f.close()
mainloop(70, 79)
f = open("progress.txt", "a+")
f.write('70,79')
f.close()
mainloop(80, 89)
f = open("progress.txt", "a+")
f.write('80,89')
f.close()
mainloop(90, 99)
f = open("progress.txt", "a+")
f.write('90,99')
f.close()
