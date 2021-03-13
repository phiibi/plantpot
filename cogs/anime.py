#anime.py

import json
import asyncio
import random
import requests
from math import ceil, floor
from re import fullmatch

async def pickcharacter(t, b, r):
    url = await getanime(t, b, r)
    return url

async def getanime(topbound, bottombound, rarity):
    with open('cogs/anime/anime_cache.json', 'r') as file:
        d = json.loads(file.read())
    shows = d['sfw']
    c = {"characters": []}

    if rarity == 1:
        r = random.randrange(0, 19)
        d = requests.get('https://api.jikan.moe/v3/search/anime?q=&order_by=members&sort=desc&page=1')
        d = d.json()
        s = d['results'][r]
        c = await getshowcharacters(s['mal_id'])
    if rarity == 2:
        r = random.randrange(20, 99)
        p = ceil((r+1)/50)
        d = requests.get(f'https://api.jikan.moe/v3/search/anime?q=&order_by=members&sort=desc&page={p}')
        d = d.json()
        s = d['results'][r-(floor(r/50)*50)]
        c = await getshowcharacters(s['mal_id'])
    if rarity == 3:
        r = random.randrange(100, 249)
        p = ceil((r+1)/50)
        d = requests.get(f'https://api.jikan.moe/v3/search/anime?q=&order_by=members&sort=desc&page={p}')
        d = d.json()
        print(d)
        s = d['results'][r-(floor(r/50)*50)]
        c = await getshowcharacters(s['mal_id'])
    else:
        while not c['characters']:
            id = random.choice(shows)
            s = await getshow(id)
            if bottombound < s['members'] <= topbound:
                c = await getshowcharacters(id)
                if not c['characters']:
                    shows.remove(id)
                    await asyncio.sleep(7)
            elif s['members'] < 10000:
                shows.remove(id)
                await asyncio.sleep(7)
            elif s['members'] <= bottombound or s['members'] > topbound:
                pass
    d.update({"sfw": shows})
    with open('cogs/anime/anime_cache.json', 'w') as file:
        json.dump(d, file)

    ch = await getcharacter(c)

    if ch:
        r = {"title": s['title'],
             "character_url": ch['image_url'],
             "character_name": ch['name']}
        return r
    else:
        return await getanime(topbound, bottombound, rarity)

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
