#flowers.py

import os
import json
import asyncio
import random
import time
import discord

from cogs import serversettings, imageposting
from discord.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def flowerevent(self, ctx):
        await ctx.message.delete()
        cd = await serversettings.getcd(self, ctx)
        start = time.time()
        while True:
            await asyncio.sleep(5)
            if imageposting.Imageposting.checktime(self, start):
                r = random.random()
                if r <= 0.00001:
                    p = 500
                    x = 0
                elif r <= 0.0025:
                    p = 250
                    x = 1
                elif r <= 0.01:
                    p = 150
                    x = 2
                elif r <= 0.015:
                    p = 100
                    x = 3
                elif r <= 0.02:
                    p = 75
                    x = 4
                elif r <= 0.03:
                    p = 50
                    x = 5
                elif r <= 0.05:
                    p = 25
                    x = 6
                elif r <= 0.1:
                    p = 10
                    x = 7
                elif r <= 0.2:
                    p = 5
                    x = 8
                else:
                    p = 1
                    x = 9

        async def getflower(self, ctx, rarity):
            with open(f'cogs/flowers.json', 'r') as file:
                d = json.loads(file.read())
            if rarity == 0:
                return {"plant": "https://i.imgur.com/I9SPukW.jpg"}
            elif rarity == 1:

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