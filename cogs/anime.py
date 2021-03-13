#anime.py

import asyncio
import random
import requests
from math import ceil, floor
from re import fullmatch, split

async def pickcharacter(r):
    url = await getanime(r)
    return url

async def getanime(rarity):

    c = {'characters': []}
    rarities = {1: {"upper": 4,
                    "lower": 0},
                2: {"upper": 19,
                    "lower": 5},
                3: {"upper": 49,
                    "lower": 20},
                4: {"upper": 99,
                    "lower": 50},
                5: {"upper": 249,
                    "lower": 100},
                6: {"upper": 4950,
                    "lower": 4200},
                7: {"upper": 4199,
                    "lower": 3700},
                8: {"upper": 3699,
                    "lower": 3300},
                9: {"upper": 3299,
                    "lower": 250}}
    l = rarities[rarity]['lower']
    u = rarities[rarity]['upper']

    while not c['characters']:
        s = await findshow(l, u)
        c = await getshowcharacters(s['mal_id'])

    ch = await getcharacter(c)

    if ch:
        r = {"title": s['title'],
             "character_url": ch['image_url'],
             "character_name": sanitisename(ch['name'])}
        return r
    else:
        return await getanime(rarity)


async def findshow(lower, upper):
    rating = 'Rx'
    try:
        while rating == 'Rx':
            r = random.randrange(lower, upper)
            p = ceil((r+1)/50)
            d = requests.get(f'https://api.jikan.moe/v3/search/anime?q=&order_by=members&sort=desc&page={p}')
            d = d.json()
            s = d['results'][r-(floor(r/50)*50)]
            rating = s['rated']
    except requests.exceptions.Timeout:
        if not retry(findshow(lower, upper)):
            print('timed out')
    except response.exceptions.HTTPError as e:
        raise SystemExit(e)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    return s


async def getshowcharacters(id):
    try:
        print(id)
        response = requests.get(f'https://api.jikan.moe/v3/anime/{id}/characters_staff')
        response.raise_for_status()
    except requests.exceptions.Timeout:
        if not retry(getshowcharacters(id)):
            print('timed out')
    except response.exceptions.HTTPError as e:
        raise SystemExit(e)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    r = response.json()
    return r


async def getshow(id):
    try:
        print(id)
        response = requests.get(f'https://api.jikan.moe/v3/anime/{id}')
        response.raise_for_status()
    except requests.exceptions.Timeout:
        r = await retry(getshowcharacters(id))
        if not r:
            print('timed out')
    except response.exceptions.HTTPError as e:
        raise SystemExit(e)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    r = response.json()
    return r


async def getcharacter(data):
    characters = data['characters']
    for i in range(5):
        r = random.choice(characters)
        if not fullmatch('.*(questionmark).*', r['image_url']):
            return r
    return False

def sanitisename(name):
    sp = split(",", name)
    if len(sp) == 2:
        new = f'{sp[1]} {sp[0]}'
        return new
    return name


async def retry(func, *args, retry_count=5, delay=5, **kwargs):
    for _ in range(retry_count):
        try:
            response = func(*args)
            if response:
                return response
        except response.exceptions.Timeout as e:
            pass
        await asyncio.sleep(delay)
    return response

response = requests.get(f'https://api.jikan.moe/v3/search/anime?q=&order_by=members&sort=desc&page={1}')
print(response.json())