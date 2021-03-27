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
        if await leaderboard.Leaderboard.checkuser(self, ctx.message.author.id, d):
            for user in d['users']:
                if ctx.message.author.id == user['userid']:
                    inventory = ''
                    if len(user['images']) < 10:
                        for item in range(0, len(user['images'])):
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
                            if temp == len(user['images']):
                                temp -= (temp % 10)
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
                                                if temp % 10 == 0:
                                                    temp -= 20
                                                else:
                                                    temp -= 10 + (temp % 10)
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
                            if temp == len(user['image_name']):
                                temp -= (temp % 10)
                            inventory = ''
                            for item in range(temp, len(user['image_name'])):
                                inventory += f'{item+1}. **' + user['image_name'][item] + '**\n'
                                temp += 1
                                if (item + 1) % 10 == 0:
                                    temp = item + 1
                                    break
                            embed = f_embed
                            embed.description = inventory
                            embed.set_footer(text='page {0}/{1}'.format(ceil(temp/10), ceil(len(user['image_name'])/10)))
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
                                                    if temp % 10 == 0:
                                                        temp -= 20
                                                    else:
                                                        temp -= 10 + (temp % 10)
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
        if user == ctx.message.author:
            return await ctx.send('you can\'t give yourself something!')
        for u in d['users']:
            if ctx.message.author.id == u['userid']:
                if u['images'].count(image) >= 1:
                    await ctx.send(f'{user.mention}! {um} wants to give you {image}, do you accept? '
                                    '[(y)es/(n)o]')
                    def check(m):
                        return m.channel == ctx.channel and m.author == user

                    try:
                        while True:
                            m = await self.bot.wait_for('message', check=check, timeout=60)
                            if m.content.lower() in ['y', 'yes']:
                                await self.transferimage(ctx.message.author.id, user.id, image, sid)
                                return await ctx.send(f'congratulations {user.mention}, you\'re the proud new owner of {image}')
                            if m.content.lower() in ['n', 'no']:
                                return await ctx.send(f'uh oh, {user.mention} doesn\'t want {um}\'s {image}')
                    except asyncio.TimeoutError:
                        return await ctx.send(f'uh oh, {user.mention} didn\'t respond in time, please try again when they\'re not busy')
                else:
                    return await ctx.send(f'you don\'t have any {image}s to give out!')
        else:
            await ctx.send('you don\'t have anything to give out! please try collecting some items first')

    @commands.command(name='animegive', help='gives an item from your inventory to another user')
    async def animegive(self, ctx, user: discord.Member, *, image):
        sid = ctx.guild.id
        with open(f'cogs/leaderboards/a{sid}.json', 'r') as file:
            d = json.loads(file.read())
        um = ctx.message.author.mention
        if user == self.bot.user:
            return await ctx.send('thank you but i could never accept this gift')
        if user == ctx.message.author:
            return await ctx.send ('you can\'t give yourself something!')
        for u in d['users']:
            if ctx.message.author.id == u['userid']:
                if u['image_name'].count(image) >= 1:
                    await ctx.send(f'{user.mention}! {um} wants to give you {image}, do you accept? '
                                   '[(y)es/(n)o]')
                    def check(m):
                        return m.channel == ctx.channel and m.author == user

                    try:
                        m = await self.bot.wait_for('message', check=check, timeout=60)
                        if m.content.lower() in ['y', 'yes']:
                            await self.atransferimage(ctx.message.author.id, user.id, image, sid)
                            return await ctx.send(f'congratulations {user.mention}, you\'re the proud new owner of {image}')
                        if m.content.lower() in ['n', 'no']:
                            return await ctx.send(f'uh oh, {user.mention} doesn\'t want {um}\'s {image}')
                    except asyncio.TimeoutError as e:
                        return await ctx.send(f'uh oh, {user.mention} didn\'t respond in time, please try again when they\'re not busy')
                else:
                    return await ctx.send(f'you don\'t have any {image}s to give out!')
        else:
            await ctx.send('you don\'t have anything to give out! please try collecting some items first')

    @commands.command(name='trade', hidden=True)
    async def trade(self, ctx, user: discord.Member):
        sid = ctx.guild.id
        usr = ctx.message.author
        offertxt = ""

        with open(f'cogs/leaderboards/a{sid}.json', 'r') as file:
            d = json.loads(file.read())
        if user == self.bot.user:
            return await ctx.send('thank you but i have no worldly desires, other than sunlight of course')
        elif user == usr:
            return await ctx.send('you can\'t trade with yourself!')
        await ctx.send(f'{user.mention}! {usr.mention} would like to trade with you, are you available? [(y)es/(n)o]')

        def check(m):
            return m.channel == ctx.channel and m.author == usr
        try:
            m = await self.bot.wait_for('message', check=check, timeout=60)
            if m.content.lower() in ['y', 'yes']:
                await ctx.send(f'{usr.mention}, it\'s your turn to make an offer')
                offer = await Inventory.tradeloop(self, ctx, usr)
            if m.content.lower() in ['n', 'no']:
                return await ctx.send(f'uh oh, {usr.mention} doesn\'t want to trade after all')
        except asyncio.TimeoutError as e:
            return await ctx.send(f'uh oh, {usr.mention} didn\'t respond in time, please try again when they\'re not busy')

        def check(m):
            return m.channel == ctx.channel and m.author == user
        try:
            m = await self.bot.wait_for('message', check=check, timeout=60)
            if m.content.lower() in ['y', 'yes']:
                await ctx.send(f'{user.mention}, it\'s your turn to make an offer')
                offer1 = await Inventory.tradeloop(self, ctx, user)
            if m.content.lower() in ['n', 'no']:
                return await ctx.send(f'uh oh, {user.mention} doesn\'t want to trade after all')
        except asyncio.TimeoutError as e:
            return await ctx.send(f'uh oh, {user.mention} didn\'t respond in time, please try again when they\'re not busy')
        embed = discord.Embed()
        embed.title = f'{usr.display_name}\'s offer'
        for item in offer:
            offertxt += item + '\n'
        embed.description = offertxt

    async def tradeloop(self, ctx, user):
        with open(f'cogs/leaderboards/a{ctx.guild.id}.json', 'r') as file:
            d = json.loads(file.read())
        for user in d['users']:
            if user['userid'] == user.id:
                remaininginv = user['image_name']
        if not remaininginv:
            return remaininginv
        temp = []
        while True:
            await Inventory.animeinventory(self, ctx)
            def check(m):
                return m.channel == ctx.channel and m.author == user
            while True:
                await ctx.send('what you like to offer? if you would not like to offer anything, please say `no offer`')
                try:
                    m = await self.bot.wait_for('message', check=check, timeout=90)
                    if leaderboard.AnimeLeaderboard.checkimage(self, user.id, ctx.guild.id, m):
                        temp.append(m)
                        remaininginv.remove(m)
                        if not remaininginv:
                            await ctx.send('you have nothing left to trade!')
                            return temp
                        break
                    if m.content.lower() == 'no offer':
                        break
                    else:
                        await ctx.send('i couldn\'t find that, please check you have the character or that you spelt their name correctly')
                        pass
                except asyncio.TimeoutError:
                    return await ctx.send('uh oh, we ran out of time, please try again!')
            await ctx.send('would you like to offer anything else? [(y)es/(n)o]')
            try:
                m = await self.bot.wait_for('message', check=check, timeout=90)
                if m.content.lower() in ['y', 'yes']:
                    return temp
                if m.content.lower() in ['n', 'no']:
                    pass
            except asyncio.TimeoutError:
                await ctx.send('uh oh, we ran out of time, please try again!')
                return None

    async def transferimage(self, uid0, uid1, image, sid):
        await leaderboard.Leaderboard.addpoint(self, uid1, sid, image, 0)
        with open(f'cogs/leaderboards/lb{sid}.json', 'r') as file:
            d = json.loads(file.read())
        for i, user in enumerate(d['users']):
            if user['userid'] == uid0:
                images = user['images']
                images.remove(image)
                d['users'][i].update({"userid": uid0,
                                      "points": user['points'],
                                      "images": images})
                break
        with open(f'cogs/leaderboards/lb{sid}.json', 'w') as file:
            json.dump(d, file)

    async def atransferimage(self, uid0, uid1, imagename, sid):
        with open(f'cogs/leaderboards/a{sid}.json', 'r') as file:
            d = json.loads(file.read())
        for i, user in enumerate(d['users']):
            if user['userid'] == uid0:
                n = user['image_name'].index(imagename)
                image_n = user['image_name']
                image_u = user['image_url']
                await leaderboard.AnimeLeaderboard.addpoint(self, uid1, sid, image_u[n], image_n[n], 0)
                image_n.remove(imagename)
                image_u.pop(n)
                d['users'][i].update({"userid": uid0,
                                      "points": user['points'],
                                      "image_name": image_n})
                break
        with open(f'cogs/leaderboards/a{sid}.json', 'w') as file:
            json.dump(d, file)

    async def getpoints(self, image, hadbefore):
        with open(f'cogs/flowers.json', 'r') as file:
            f = json.loads(file.read())
        for cat in f:
            for flower in f[cat]:
                t = list(flower.items())
                if t[0][0] == image:
                    temp = {"image": {"url": t[0][1], "desc": t[0][0]}}
    @give.error
    async def giveerror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send("please format as `.give [user] [item]`")

def setup(bot):
    bot.add_cog(Inventory(bot))



