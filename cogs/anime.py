#anime.py

import asyncio
import random
import requests
import discord
import time
import operator
import json

from math import ceil, floor
from re import fullmatch, split
from cogs import profile, leaderboard, imageposting, checkers
from discord.ext import commands

class Anime(commands.Cog):
    version = '0.1'
    def __init__(self, bot):
        self.bot = bot
        self.emoji = '\U0001F338'

    @commands.group(help='anime related commands', hidden=True)
    async def anime(self, ctx):
        if ctx.invoked_subcommand is None:
                return

    @anime.command(name='event', help='starts an event using anime characters')
    @commands.max_concurrency(1, commands.BucketType.guild)
    @checkers.is_guild_owner()
    async def anime_event(self, ctx):
        await ctx.message.delete()
        cd = 60

        start = time.time()
        c = checkers.SpamChecker()
        while True:
            await asyncio.sleep(5)
            if imageposting.Imageposting.checktime(self, start):
                r = random.random()
                if ctx.guild.id == 813532137050341407 or ctx.guild.id == 502944697225052181:
                    if r <= 0.005:
                        p = 300
                        x = 1
                    elif r <= 0.0075:
                        p = 150
                        x = 2
                    elif r <= 0.013:
                        p = 75
                        x = 3
                    elif r <= 0.035:
                        p = 25
                        x = 4
                    elif r <= 0.075:
                        p = 10
                        x = 5
                    elif r <= 0.15:
                        p = 5
                        x = 6
                    else:
                        p = 1
                        x = 7
                    ac = await getcharacterbyrarity(x)
                    rarities = {1: "legendary", 2: "mythic", 3: "epic", 4: "ultra rare", 5: "rare", 6: "uncommon", 7: "common"}
                else:
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
                    ac = await pickcharacter(x)
                    rarities = {1: "legendary popular", 2: "mythic popular", 3: "epic popular", 4: "rare popular", 5: "uncommon popular", 6: "epic obscure", 7: "rare obscure", 8: "uncommon obscure", 9: "common"}

                embed = discord.Embed()
                name = ac['character_name']
                if name[0] == " ":
                    name = name[1:]
                url = ac['character_url']
                embed.add_field(name=name, value=ac['title'])
                embed.set_image(url=url)
                pst = await ctx.send(embed=embed)
                await pst.add_reaction('<:frogsmile:817589614905917440>')
                await pst.add_reaction('\U0001F504')
                while True:
                    reroll = False
                    def check(r, u):
                        if r.message.id == pst.id and ((str(r.emoji) == '<:frogsmile:817589614905917440>' and u != self.bot.user) or (str(r.emoji) == '\U0001F504' and r.count == 4)):
                            return r, u
                    try:
                        r, usr = await self.bot.wait_for('reaction_add', check=check, timeout=14400)
                    except asyncio.TimeoutError:
                        return await ctx.send('Event timed out due to inactivity, please ask a user with `manage server` permissions to restart the event using `.anime event`')
                    if str(r) == '\U0001F504':
                        reroll = True
                        break
                    else:
                        if leaderboard.AnimeLeaderboard.checkimage(self, usr.id, ctx.guild.id, name):
                            await ctx.send(f'{usr.mention}! You already have this character! If you and 2 other users react \U0001F504 then you will reroll this character')
                            await r.remove(usr)
                        elif await c.checkuser(ctx, usr.id) and (ctx.guild.id == 813532137050341407 or ctx.guild.id == 502944697225052181):
                            await ctx.send(f'hold up {usr.mention}, you\'ve collected a character too recently, please wait a second to give other users a chance!')
                            await r.remove(usr)
                        #elif await checkuserblacklist(usr.id):
                        #    await ctx.send(f'hold up {usr.mention}, you\'ve been blacklisted from plant, please visit my server to appeal your ban')
                        #    await r.remove(usr)
                        else:
                            break
                if reroll:
                    await ctx.send('you have decided to reroll this character')
                    await ctx.send('no users get any points')
                else:
                    await leaderboard.AnimeLeaderboard.addpoint(self, usr.id, ctx.guild.id, url, name, p)
                    await profile.Profile.addpoint(self, usr.id, p)
                    vowels = ['a', 'e', 'i', 'o', 'u']
                    r = rarities[x]
                    if r[0] in vowels:
                        await ctx.send(f'{self.emoji} {usr.mention}**, you just picked up an {r} character!** {self.emoji}')
                    else:
                        await ctx.send(f'{self.emoji} {usr.mention}**, you just picked up a {r} character!** {self.emoji}')
                    if p == 1:
                        await ctx.send('**you\'ve earned 1 point!**')
                    else:
                        await ctx.send(f'**you\'ve earned {p} points!**')
                await asyncio.sleep(cd)
                await c.unloadusers(ctx)
                start = time.time()
                print('restarting countdown')

    @anime.command(name='rarity', help='displays different rarities, their chances, and points given')
    async def rarity(self, ctx):
        if ctx.guild.id == 813532137050341407 or ctx.guild.id == 502944697225052181:
            temp = ['Legendary **(300)** *(Top 50 characters on MAL)*: 0.5%',
                    'Mythic **(150)** *(Top 51 - 150 characters on MAL)*: 0.75%',
                    'Epic **(100)** *(Top 151 - 300 characters on MAL)*: 1.3%',
                    'Ultra Rare **(25)** *(Top 300 - 550 characters on MAL)*: 3.5%',
                    'Rare **(10)** *(Top 551 - 1050 characters on MAL)*: 7.5%',
                    'Uncommon **(5)** *(Top 1051 - 2050 characters on MAL)*: 15%',
                    'Common **(1)** *(Top 2051 - 5000 characters on MAL)*: 71.45%']
        else:
            temp = ["Legendary popular **(100)** *(Top 5 anime on MAL)*: 0.5%",
                    "Mythic popular **(50)** *(Top 5-19 anime on MAL)*: 1.5%",
                    "Epic popular **(10)** *(Top 20-49 anime on MAL)*: 3.5%",
                    "Rare popular **(7)** *(Top 50-99 anime on MAL)*: 4.5%",
                    "Uncommon popular **(5)** *(Top 100- 249 anime on MAL)*: 12.5%",
                    "Common **(1)** *(Between the top 250th show and 25,000 watches on MAL)*: 62.5%",
                    "Uncommon obscure **(5)** *(Between 20,000 and 25,000 watches on MAL)*: 7.5%",
                    "Rare obscure **(7)** *(Between 15,000 and 20,000 watches on MAL)*: 5%",
                    "Epic obscure **(10)** *(Between 10,000 and 15,000 watches on MAL)*: 2.5%"]
        embed = discord.Embed()
        embed.title = "Anime rarities"
        embed.description = '\n'.join([i for i in temp])
        await ctx.send(embed=embed)

    @anime.command(name='blacklist', hidden=True)
    @checkers.is_plant_owner()
    async def addblacklist(self, ctx, cid: int):
        with open(f'cogs/characters_blacklist.json', 'r') as file:
            d = json.loads(file.read())
        if d['id'].count(cid):
            return await ctx.send('character already blacklisted')
        d['id'].append(cid)
        await ctx.send(f'blacklisted {cid}')
        with open('cogs/characters_blacklist.json', 'w') as file:
            json.dump(d, file)


async def pickcharacter(r):
    url = await getanime(r)
    return url

async def checkblacklist(id):
    with open(f'cogs/characters_blacklist.json', 'r') as file:
        d = json.loads(file.read())
    if d['id'].count(id) >= 1:
        return True
    else:
        return False

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

async def getcharacterbyrarity(rarity):
    rarities = {1: {"upper": 49,
                    "lower": 0},
                2: {"upper": 149,
                    "lower": 50},
                3: {"upper": 299,
                    "lower": 150},
                4: {"upper": 549,
                    "lower": 300},
                5: {"upper": 1049,
                    "lower": 550},
                6: {"upper": 2049,
                    "lower": 1050},
                7: {"upper": 4999,
                    "lower": 2050}}

    l = rarities[rarity]['lower']
    u = rarities[rarity]['upper']

    c = await findcharacter(l, u)
    s = await parseshow(c)

    r = {"title": s['name'],
         "character_url": c['image_url'],
         "character_name": sanitisename(c['title'])}

    return r

async def findcharacter(lower, upper):
    try:
        temp = []
        while temp == []:
            r = random.randrange(lower, upper)
            p = floor((r+1)/50)
            d = requests.get(f'https://api.jikan.moe/v3/top/characters/{p}')
            d = d.json()
            c = d['top'][r-(floor(r/50)*50)]
            temp = c['animeography']
            if await checkblacklist(c['mal_id']):
                print(c['title'])
                print('bad character')
                temp = []
    except requests.exceptions.Timeout:
        if not retry(findcharacter(lower, upper)):
            print('timed out')
    except requests.exceptions.HTTPError as e:
        raise SystemExit(e)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)
    return c

async def parseshow(c):
    shows = c['animeography']
    shows.sort(key=operator.itemgetter('mal_id'))
    return shows[0]


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

async def checkuserblacklist(userid):
    with open(f'cogs/userblacklist.json', 'r') as file:
        d = json.loads(file.read())
    if d['id'].count(userid):
        return True
    return False

def setup(bot):
    bot.add_cog(Anime(bot))

