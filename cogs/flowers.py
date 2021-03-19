#flowers.py

import os
import json
import asyncio
import random
import time
import discord

from cogs import serversettings, imageposting, leaderboard, profile, checkers
from discord.ext import commands

class Flower(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emoji = '\U0001F338'

    async def flowerevent(self, ctx):
        await ctx.message.delete()
        cd = await serversettings.getcd(self, ctx)
        start = time.time()
        c = checkers.SpamChecker()
        while True:
            await asyncio.sleep(5)
            if imageposting.Imageposting.checktime(self, start):
                r = random.random()
                if r <= 0.00001:
                    p = 500
                    x = 0
                elif r <= 0.0025:
                    p = 300
                    x = 1
                elif r <= 0.01:
                    p = 200
                    x = 2
                elif r <= 0.015:
                    p = 100
                    x = 3
                elif r <= 0.025:
                    p = 50
                    x = 4
                elif r <= 0.04:
                    p = 25
                    x = 5
                elif r <= 0.1:
                    p = 10
                    x = 6
                elif r <= 0.2:
                    p = 5
                    x = 7
                else:
                    p = 1
                    x = 8
                temp = await Flower.getflower(self, ctx, x)
                image = list(temp.items())[0]
                rarities = {0: "ultra special amazing", 1: "legendary", 2: "mythic", 3: "epic", 4: "plant's favourite", 5: "ultra rare", 6: "rare", 7: "uncommon", 8: "common"}
                embed = discord.Embed()
                embed.set_image(url=image[1])
                post = await ctx.send(embed=embed)
                await post.add_reaction(self.emoji)
                async def check(r, u):
                    if str(r.emoji) == self.emoji and r.message.id == p.id and u != self.bot.user and not c.checkuser(u.id):
                        return r, u
                    if c.checkuser(self, ctx, u.id):
                        await ctx.send('hold up! you\'ve collected something too recently, please wait for a moment')
                r, usr = await self.bot.wait_for('reaction_add', check=await check)
                if leaderboard.Leaderboards.checkimage(self, usr.id, ctx.guild.id, image[0]):
                    coll = True
                    if x == 0:
                        p = 200
                    elif x == 1:
                        p = 100
                    elif x == 2:
                        p = 60
                    elif x == 3:
                        p = 30
                    elif x == 4:
                        x = 20
                    elif x == 5:
                        p = 10
                    elif x == 6:
                        p = 5
                    elif x == 7:
                        p = 2
                    else:
                        p = 1
                await leaderboard.Leaderboard.addpoint(self, usr.id, ctx.guild.id, image[0], p)
                await profile.Profile.addpoint(self, usr.id, p)
                r = rarities[x]
                if x == 1 or x == 2 or x == 4 or x == 6 or x == 8:
                    await ctx.send(f'{self.emoji} {usr.mention}**, you just picked up a {r} flower!** {self.emoji}')
                else:
                    await ctx.send(f'{self.emoji} {usr.mention}**, you just picked up an {r} flower!** {self.emoji}')
                if p == 1:
                    await ctx.send('**you\'ve earned 1 point!**')
                else:
                    if coll:
                        await ctx.send(f'**as you\'ve collected this before, you\'ve earned {p} points**')
                    else:
                        await ctx.send(f'**you\'ve earned {p} points!**')
                await asyncio.sleep(cd)
                c.unloadusers(self, ctx)
                start = time.time()

        async def getflower(self, ctx, rarity):
            with open(f'cogs/flowers.json', 'r') as file:
                d = json.loads(file.read())
            if rarity == 0:
                return {"plant": "https://i.imgur.com/I9SPukW.jpg"}
            elif rarity == 1:
                temp = d['Legendary']
                return random.choice(temp)
            elif rarity == 2:
                temp = d['Mythic']
                return random.choice(temp)
            elif rarity == 3:
                temp = d['Epic']
                return random.choice(temp)
            elif rarity == 4:
                temp = d["Plant's Favourites"]
                return random.choice(temp)
            elif rarity == 5:
                temp = d['Ultra Rare']
                return random.choice(temp)
            elif rarity == 6:
                temp = d['Rare']
                return random.choice(temp)
            elif rarity == 7:
                temp = d['Uncommon']
                return random.choice(temp)
            elif rarity == 8:
                temp = d['Common']
                return random.choice(temp)

        start = time.time()
        while True:
            await asyncio.sleep(5)
            if imageposting.Imageposting.checktime(self, start):
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
                while True:
                    def check(r, u):
                        if str(r.emoji) == '<:frogsmile:817589614905917440>' and r.message.id == pst.id and u != self.bot.user:
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
                print('restarting countdown')