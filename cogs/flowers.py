#flowers.py

import os
import json
import asyncio
import random
import time
import discord

from cogs import imageposting, leaderboard, profile, checkers
from discord.ext import commands

class Flower(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emoji = '\U0001F338'

    @commands.command(name='flowerevent', hidden=True)
    @commands.max_concurrency(1, commands.BucketType.guild)
    async def flowerevent(self, ctx):
        await ctx.message.delete()
        cd = 60
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
                elif r <= 0.0075:
                    p = 200
                    x = 2
                elif r <= 0.015:
                    p = 100
                    x = 3
                elif r <= 0.025:
                    p = 50
                    x = 4
                elif r <= 0.05:
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
                rarities = {0: "ultra super amazing", 1: "legendary", 2: "mythic", 3: "epic", 4: "plant's favourite", 5: "ultra rare", 6: "rare", 7: "uncommon", 8: "common"}
                embed = discord.Embed()
                embed.title = (image[0])
                embed.set_image(url=image[1])
                post = await ctx.send(embed=embed)
                await post.add_reaction(self.emoji)
                while True:
                    def check(r, u):
                        if str(r.emoji) == self.emoji and r.message.id == post.id and u != self.bot.user:
                            return r, u

                    r, usr = await self.bot.wait_for('reaction_add', check=check)
                    if await c.checkuser(ctx, usr.id):
                        await ctx.send(f'hold up {usr.mention}, you\'ve collected a flower too recently, please wait a second to give other users a chance!')
                        await r.remove(usr)
                    else:
                        break
                coll = False
                if leaderboard.Leaderboard.checkimage(self, usr.id, ctx.guild.id, image[0]):
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
                        p = 20
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
                if x == 1 or x == 2 or x == 6 or x == 8:
                    await ctx.send(f'{self.emoji} {usr.mention}**, you just picked up a {r} flower!** {self.emoji}')
                elif x == 4:
                    await ctx.send(f'{self.emoji} {usr.mention}**, you just picked up one of {r} flowers!** {self.emoji}')
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
                await c.unloadusers(ctx)
                print('restarting countdown')
                start = time.time()

    @commands.command(name='flowereventmean', hidden=True)
    @commands.max_concurrency(1, commands.BucketType.guild)
    async def flowereventmean(self, ctx):
        await ctx.message.delete()
        cd = 60
        start = time.time()
        c = checkers.SpamChecker()
        bls = checkers.blacklistSpam()
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
                elif r <= 0.0075:
                    p = 200
                    x = 2
                elif r <= 0.015:
                    p = 100
                    x = 3
                elif r <= 0.025:
                    p = 50
                    x = 4
                elif r <= 0.05:
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
                rarities = {0: "ultra super amazing", 1: "legendary", 2: "mythic", 3: "epic", 4: "plant's favourite", 5: "ultra rare", 6: "rare", 7: "uncommon", 8: "common"}
                embed = discord.Embed()
                embed.title = (image[0])
                embed.set_image(url=image[1])
                post = await ctx.send(embed=embed)
                await post.add_reaction(self.emoji)
                while True:
                    def check(r, u):
                        if str(r.emoji) == self.emoji and r.message.id == post.id and u != self.bot.user:
                            return r, u

                    r, usr = await self.bot.wait_for('reaction_add', check=check)
                    if await c.checkuser(ctx, usr.id):
                        if await bls.adduser(usr.id):
                            await ctx.send(f'i\'m sorry {usr.mention} but you\'re being a little too eager! to give other users and me a chance, your cooldown has been reset, please be more patient in the future!')
                            await c.adduser(ctx, usr.id)
                        else:
                            await ctx.send(f'hold up {usr.mention}, you\'ve collected a flower too recently, please wait a second to give other users a chance!')
                        await r.remove(usr)
                    else:
                        break
                coll = False
                if leaderboard.Leaderboard.checkimage(self, usr.id, ctx.guild.id, image[0]):
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
                        p = 20
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
                if x == 1 or x == 2 or x == 6 or x == 8:
                    await ctx.send(f'{self.emoji} {usr.mention}**, you just picked up a {r} flower!** {self.emoji}')
                elif x == 4:
                    await ctx.send(f'{self.emoji} {usr.mention}**, you just picked up one of {r} flowers!** {self.emoji}')
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
                await c.unloadusers(ctx)
                print('restarting countdown')
                start = time.time()

    async def getflower(self, ctx, rarity):
        with open(f'cogs/flowers.json', 'r') as file:
            d = json.loads(file.read())
        if rarity == 0:
            return {"me!!": "https://i.imgur.com/I9SPukW.jpg"}
        elif rarity == 1:
            temp = d['Legendary']
            return random.choice(temp)
        elif rarity == 2:
            temp = d['Mythic']
            return random.choice(temp)
        elif rarity == 3:
            temp = d['Epic']
            x = random.choice(temp)
            print(x)
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

def setup(bot):
    bot.add_cog(Flower(bot))
