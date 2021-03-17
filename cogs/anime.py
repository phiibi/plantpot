#anime.py

import asyncio
import random
import requests
import discord
import time

from math import ceil, floor
from re import fullmatch, split
from discord.ext import commands

class Anime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

"""@anime.command(name='event', help='starts an event using anime characters')
@commands.max_concurrency(1, commands.BucketType.guild)
@commands.is_owner()
async def anime_event(self, ctx):
    await ctx.message.delete()
    cd = 60

    start = time.time()
    while True:
        await asyncio.sleep(5)
        if self.checktime(start):
            r = random.random()
            if r >= 0.995:
                p = 100
                x = 1
            elif r >= 0.985:
                p = 50
                x = 2
            elif r >= 0.965:
                p = 10
                x = 3
            elif r >= 0.925:
                p = 7
                x = 4
            elif r >= 0.8:
                p = 5
                x = 5
            elif r <= 0.025:
                p = 10
                x = 6
            elif r <= 0.075:
                p = 7
                x = 7
            elif r <= 0.15:
                p = 5
                x = 8
            else:
                p = 1
                x = 9
            ac = await anime.pickcharacter(x)
            rarities = {1: "legendary popular", 2: "mythic popular", 3: "epic popular", 4: "rare popular", 5: "uncommon popular", 6: "epic obscure", 7: "rare obscure", 8: "uncommon obscure", 9: "common"}
            embed = discord.Embed()
            name = ac['character_name']
            if name[0] == " ":
                name = name[1:]
            url = ac['character_url']
            embed.add_field(name=name, value=ac['title'])
            embed.set_image(url=url)
            pst = await ctx.send(embed=embed)
            await pst.add_reaction('\U00002B05')
            while True:
                def check(r, u):
                    if str(r.emoji) == '\U00002B05' and r.message.id == pst.id and u != self.bot.user:
                        return r, u
                r, usr = await self.bot.wait_for('reaction_add', check=check)
                if leaderboard.AnimeLeaderboard.checkimage(self, usr.id, ctx.guild.id, name):
                    await ctx.send(f'{usr.mention}! You already have this character!')
                    await r.remove(usr)
                else:
                    break
            await leaderboard.AnimeLeaderboard.addpoint(self, usr.id, ctx.guild.id, url, name, p)
            await profile.Profile.addpoint(self, usr.id, p)
            r = rarities[x]
            if x == 1 or x == 2 or x == 4 or x == 7 or x ==9:
                await ctx.send(f'{self.emoji} {usr.mention}**, you just picked up a {r} character!** {self.emoji}')
            else:
                await ctx.send(f'{self.emoji} {usr.mention}**, you just picked up an {r} character!** {self.emoji}')
            if p == 1:
                await ctx.send('**you\'ve earned 1 point!**')
            else:
                await ctx.send(f'**you\'ve earned {p} points!**')
            await asyncio.sleep(cd)
            start = time.time()
            print('restarting countdown')"""
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
    except requests.exceptions.HTTPError as e:
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
        if new[0] == " ":
            return new[1:]
        else:
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
