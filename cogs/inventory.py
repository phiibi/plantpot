#inventory.py

import json
import discord
import time
import asyncio
from math import ceil

from discord.ext import commands
from cogs import leaderboard


class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='inventory', help='displays inventory')
    async def inventory(self, ctx):
        sid = ctx.guild.id
        with open(f'cogs/leaderboards/lb{sid}.json', 'r') as file:
            d = json.loads(file.read())
        if leaderboard.Leaderboard.checkuser(self, ctx.message.author.id, d):
            for user in d['users']:
                if ctx.message.author.id == user['userid']:
                    inventory = ''
                    if len(user['images']) < 10:
                        for item in range(0,len(user['images'])):
                            inventory += '{0}. **'.format(item+1) + user['images'][item] + '**\n'
                        embed = discord.Embed()
                        embed.title = 'your inventory'
                        embed.description = inventory
                        embed.set_thumbnail(url=ctx.message.author.avatar_url_as())
                        return await ctx.send(embed=embed)
                    else:
                        start = time.time()
                        temp = 0
                        f_embed = discord.Embed()
                        f_embed.title = 'your inventory'
                        f_embed.set_thumbnail(url=ctx.message.author.avatar_url_as())
                        m = await ctx.send(embed=f_embed)
                        while True:
                            inventory = ''
                            for item in range(temp, len(user['images'])):
                                inventory += f'{item+1}. **' + user['images'][item] + '**\n'
                                temp += 1
                                if (item + 1) % 10 == 0:
                                    temp = item + 1
                                    break
                            embed = f_embed
                            embed.description = inventory
                            embed.set_footer(text='page {0}/{1}'.format(ceil(temp/10), ceil(len(user['images'])/10)))
                            await m.edit(embed=embed)
                            await m.add_reaction('\U00002B05')
                            await m.add_reaction('\U000027A1')
                            while True:
                                if time.time() - start > 120:
                                    break
                                m = await m.channel.fetch_message(m.id)
                                if m.reactions[0].count > 1:
                                    async for u in m.reactions[0].users():
                                        if u == ctx.message.author:
                                            if temp == 9:
                                                pass
                                            else:
                                                if temp < 20:
                                                    temp = 0
                                                else:
                                                    temp -= 20
                                                break
                                    await m.reactions[0].remove(ctx.message.author)
                                    break
                                if m.reactions[1].count > 1:
                                    async for u in m.reactions[1].users():
                                        if u == ctx.message.author:
                                            break
                                    await m.reactions[1].remove(ctx.message.author)
                                    break
                            if time.time() - start > 120:
                                break

    @commands.command(name='animeinventory', help='displays inventory')
    async def animeinventory(self, ctx):
        sid = ctx.guild.id
        with open(f'cogs/leaderboards/a{sid}.json', 'r') as file:
            d = json.loads(file.read())
        c = await leaderboard.Leaderboard.checkuser(self, ctx.message.author.id, d)
        if c:
            for user in d['users']:
                if ctx.message.author.id == user['userid']:
                    inventory = ''
                    if len(user['image_name']) < 10:
                        for item in range(0, len(user['image_name'])):
                            inventory += '{0}. **'.format(item+1) + user['image_name'][item] + '**\n'
                        embed = discord.Embed()
                        embed.title = 'your inventory'
                        embed.description = inventory
                        embed.set_thumbnail(url=ctx.message.author.avatar_url_as())
                        return await ctx.send(embed=embed)
                    else:
                        start = time.time()
                        temp = 0
                        f_embed = discord.Embed()
                        f_embed.title = 'your inventory'
                        f_embed.set_thumbnail(url=ctx.message.author.avatar_url_as())
                        m = await ctx.send(embed=f_embed)
                        while True:
                            inventory = ''
                            for item in range(temp, len(user['image_name'])):
                                inventory += f'{item+1}. **' + user['image_name'][item] + '**\n'
                                temp += 1
                                if (item + 1) % 10 == 0:
                                    temp = item + 1
                                    break
                            embed = f_embed
                            embed.description = inventory
                            embed.set_footer(text='page {0}/{1}'.format(ceil(temp/10), ceil(len(user['images'])/10)))
                            await m.edit(embed=embed)
                            await m.add_reaction('\U00002B05')
                            await m.add_reaction('\U000027A1')
                            while True:
                                if time.time() - start > 120:
                                    break
                                m = await m.channel.fetch_message(m.id)
                                if m.reactions[0].count > 1:
                                    async for u in m.reactions[0].users():
                                        if u == ctx.message.author:
                                            if temp == 9:
                                                pass
                                            else:
                                                if temp < 20:
                                                    temp = 0
                                                else:
                                                    temp -= 20
                                                break
                                    await m.reactions[0].remove(ctx.message.author)
                                    break
                                if m.reactions[1].count > 1:
                                    async for u in m.reactions[1].users():
                                        if u == ctx.message.author:
                                            break
                                    await m.reactions[1].remove(ctx.message.author)
                                    break
                            if time.time() - start > 120:
                                break

    @commands.command(name='give', help='gives an item from your inventory to another user')
    async def give(self, ctx, user: discord.Member, *, image):
        sid = ctx.guild.id
        with open(f'cogs/leaderboards/lb{sid}.json', 'r') as file:
            d = json.loads(file.read())
        um = ctx.message.author.mention
        if user == self.bot.user:
            return await ctx.send('thank you but i could never accept this gift')
        for u in d['users']:
            if ctx.message.author.id == u['userid']:
                if u['images'].count(image) >= 1:
                    await ctx.send(f'{user.mention}! {um} wants to give you {image}, do you accept? '
                                    '[(y)es/(n)o]')
                    def check(m):
                        return m.channel == ctx.channel and m.author == user

                    m = await self.bot.wait_for('message', check=check, timeout=60)

                    try:
                        if m.content.lower() in ['y', 'yes']:
                            self.transferimage(ctx.message.author.id, user.id, image, sid)
                            return await ctx.send(f'congratulations {user.mention}, you\'re a proud new owner of {image}')
                        if m.content.lower() in ['n', 'no']:
                            return await ctx.send(f'uh oh, {user.mention} doesn\'t want {um}\'s {image}')
                    except asyncio.TimeoutError:
                        return await ctx.send(f'uh oh, {user.mention} didn\'t respond in time, please try again when they\'re not busy')
                else:
                    return await ctx.send(f'you don\'t have any {image}s to give out!')
        else:
            await ctx.send('you don\'t have anything to give out! please try collecting some items first')

    @commands.command(name='animegive', help='gives an item from your inventory to another user')
    async def give(self, ctx, user: discord.Member, *, image):
        sid = ctx.guild.id
        with open(f'cogs/leaderboards/a{sid}.json', 'r') as file:
            d = json.loads(file.read())
        um = ctx.message.author.mention
        if user == self.bot.user:
            return await ctx.send('thank you but i could never accept this gift')
        for u in d['users']:
            if ctx.message.author.id == u['userid']:
                if u['image_name'].count(image) >= 1:
                    await ctx.send(f'{user.mention}! {um} wants to give you {image}, do you accept? '
                                   '[(y)es/(n)o]')
                    def check(m):
                        return m.channel == ctx.channel and m.author == user

                    m = await self.bot.wait_for('message', check=check, timeout=60)

                    try:
                        if m.content.lower() in ['y', 'yes']:
                            self.atransferimage(ctx.message.author.id, user.id, image, sid)
                            return await ctx.send(f'congratulations {user.mention}, you\'re a proud new owner of {image}')
                        if m.content.lower() in ['n', 'no']:
                            return await ctx.send(f'uh oh, {user.mention} doesn\'t want {um}\'s {image}')
                    except asyncio.TimeoutError:
                        return await ctx.send(f'uh oh, {user.mention} didn\'t respond in time, please try again when they\'re not busy')
                else:
                    return await ctx.send(f'you don\'t have any {image}s to give out!')
        else:
            await ctx.send('you don\'t have anything to give out! please try collecting some items first')

    def transferimage(self, uid0, uid1, image, sid):
        leaderboard.Leaderboard.addpoint(self, uid1, sid, image)
        with open(f'cogs/leaderboards/lb{sid}.json', 'r') as file:
            d = json.loads(file.read())
        for i, user in enumerate(d['users']):
            if user['userid'] == uid0:
                images = user['images']
                images.remove(image)
                d['users'][i].update({"userid": uid0,
                                      "points": user['points'] - 1,
                                      "images": images})
                break
        with open('cogs/leaderboard.json', 'w') as file:
            json.dump(d, file)

    def atransferimage(self, uid0, uid1, image, sid):
        leaderboard.AnimeLeaderboard.addpoint(self, uid1, image, 0)
        with open(f'cogs/leaderboards/a{sid}.json', 'r') as file:
            d = json.loads(file.read())
        for i, user in enumerate(d['users']):
            if user['userid'] == uid0:
                n = user['image_name'].index(image)
                image_n = user['image_name']
                image_u = user['image_url']
                image_n.remove('image_name')
                image_u.pop(n)
                d['users'][i].update({"userid": uid0,
                                      "points": user['points'],
                                      "image_name": image_n})
                break
        with open('cogs/leaderboard.json', 'w') as file:
            json.dump(d, file)

    @give.error
    async def giveerror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send("please format as ```.give [user] [item]```")


