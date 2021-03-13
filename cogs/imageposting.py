#imageposting.py

import discord
import random
from re import fullmatch
import time
import json
import asyncio
from cogs import leaderboard, anime, profile

from discord.ext import commands

#cog with all image posting capabilities
class Imageposting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam = False
        self.store = 'randomImages'
        self.emoji = '\U0001F338'
        self.eventcd = 5

    @commands.group(help='image related commands, ".image help" for more help')
    async def image(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('please specify a command, type ``.image help`` for more help')
            return

    @image.command(name='help', help='full help for image commands')
    async def help(self, ctx, command):
        commandhelp = {"post": "`.image post [description]` will post an image, if you give the description of one, it will post that image",
                       "add": "`.image add [image-url] [description]` will add a given image url in the format `https://i.imgur.com/{url-code}.[jpg/png/gif]` with a given description",
                       "all": "`.image all` will post all images"}
        helpstr = commandhelp.get(command)
        if helpstr is None:
            await ctx.send('please enter a valid command, type ```.image help``` for a command list')
        else:
            embed = discord.Embed()
            embed.title = f'".image {command}" help'
            embed.description = helpstr
            await ctx.send(embed=embed)


    @image.command(name='post', help='posts a random image, mostly debugging')
    async def post(self, ctx, *, desc=None):
        with open(f'cogs/{self.store}.json', 'r') as file:
            d = json.loads(file.read())
        if desc is None:
            image = random.choice(d['images'])
        else:
            for i in d['images']:
                if i['desc'] == desc:
                    image = i
                    break
            if image is None:
                await ctx.send(f'i\'m sorry but i couldn\'t find {desc}')
                return
        embed = discord.Embed()
        embed.set_image(url=image['url'])
        return [await ctx.send(embed=embed), image['desc']]

    @image.command(name='setstore', help='sets default store')
    async def setstore(self, ctx, store):
        self.store = store

    @image.command(name='add', help='adds a new image to postable images, ".image add [imgur link] [description]"')
    async def add(self, ctx, link, *, desc):
        if fullmatch('^https://i\.imgur\.com/.*(\.jpg|\.jpeg|\.png|\.gif)$', link) is None:
            return await ctx.send('please link images in the form ```https://i.imgur.com/{url-code}.[jpg/png/gif]```')

        with open(f'cogs/{self.store}.json', 'r') as file:
            d = json.loads(file.read())
        images = d['images']
        for image in images:
            if image['url'] == link:
                return await ctx.send('this image is already added!')
        images.append({"url": link,
                       "desc": desc})

        temp = {"images": images}
        with open(f'cogs/{self.store}.json', 'w') as file:
            json.dump(temp, file)
            await ctx.send('image added')

    @image.command(name='remove', help='removes images', hidden=True)
    @commands.is_owner()
    async def remove(self, ctx, link):
        with open(f'cogs/{self.store}.json', 'r') as file:
            d = json.loads(file.read())
        for image in range(len(d['images'])):
            if d['images'][image]['url'] == link:
                d['images'].pop(image)
                return await ctx.send('removed image')
        await ctx.send('image not found!')

    #posts all images
    @image.command(name='all', help='posts all images')
    async def all(self, ctx):
        with open(f'cogs/{self.store}.json', 'r') as file:
            d = json.loads(file.read())
        images = d['images']
        embed = discord.Embed()
        for image in images:
            embed.set_image(url=image['url'])
            await ctx.send(embed=embed)

    #starts posting images as over a function of time
    @image.command(name='event', help='starts an image collecting event')
    @commands.max_concurrency(1, commands.BucketType.guild)
    async def event(self, ctx):
        cd = 60
        start = time.time()
        while True:
            await asyncio.sleep(2)
            if self.checktime(start):
                p, d = await self.post(ctx)
                await p.add_reaction(self.emoji)
                def check(r, u):
                    if str(r.emoji) == self.emoji and r.message.id == p.id and u != self.bot.user:
                        return r, u
                r, usr = await self.bot.wait_for('reaction_add', check=check)
                await leaderboard.Leaderboard.addpoint(self, usr.id, ctx.guild.id, d)
                await profile.Profile.addpoint(self, usr.id, 1)
                await ctx.send(self.emoji +" " + usr.mention + '**, you just picked up ' + d + "!** " + self.emoji)
                await ctx.send('**you\'ve earned one point!**')
                await asyncio.sleep(cd)
                start = time.time()
                print('restarting countdown')

    @image.command(name='eventanime', help='starts an event using anime characters')
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.is_owner()
    async def anime_event(self, ctx):
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
                url = ac['character_url']
                embed.add_field(name=name, value=ac['title'])
                embed.set_image(url=url)
                pst = await ctx.send(embed=embed)
                await pst.add_reaction('<:frogsmile:817589614905917440>')
                def check(r, u):
                    if str(r.emoji) == '<:frogsmile:817589614905917440>' and r.message.id == pst.id and u != self.bot.user and leaderboard.AnimeLeaderboard.checkimage(u.id, ctx.guild.id, name):
                        return r, u
                r, usr = await self.bot.wait_for('reaction_add', check=check)
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
                print('restarting countdown')

    #ugly and doesn't work
    @image.command(name='stop', help='stops the spam')
    @commands.is_owner()
    async def stop(self, ctx):
        Imageposting.event.stop()

    @image.command(name='eventset', help='set up for event')
    async def setevent(self, ctx, command, mod):
        if not command is None:
            if mod is None:
                await self.help(ctx, "event")
                return
            else:
                self.proccommand(command, mod)
                return

    def checktime(self, oldtime):
        newtime = time.time()
        if random.random() < pow(0.99, newtime - oldtime):
            return True

    def proccommand(self, command, mod):
        if command == 'cooldown':
            self.eventcd = int(mod)
            return
        if command == 'emoji':
            self.emoji = mod
            return

    def getcd(self, ctx):
        with open(f'cogs/{servers}.json', 'r') as file:
            d = json.loads(file.read())
        for s in d['servers']:
            if s['serverid'] == ctx.guild.id:
                return s['cd']

    def getemoji(self, ctx):
        with open(f'cogs/{servers}.json', 'r') as file:
            d = json.loads(file.read())
        for s in d['servers']:
            if s['serverid'] == ctx.guild.id:
                return s['emoji']


    # ------------- Error handling ------------- #

    @help.error
    async def helperror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            embed = discord.Embed()
            embed.title = 'please format this command as .image help [command]'
            embed.description = """image commands are:
            **post**: posts an image
            **add**: adds an image
            **all**: posts all images
            **event**: posts randomly on a timer
            **stop**: stops event"""

            await ctx.send(embed=embed)

    @post.error
    async def posterror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await self.help(ctx, "post")

    @add.error
    async def adderror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await self.help(ctx, "add")

    @all.error
    async def allerror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await self.help(ctx, "all")

    @event.error
    async def eventerror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await self.help(ctx, "event")
        if isinstance(error, commands.MaxConcurrencyReached):
            await ctx.send('You\'ve reached the maximum number of times you can start an event! Please end one before trying again')
