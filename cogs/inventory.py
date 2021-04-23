#inventory.py

import json
import discord
import asyncio
import operator
from math import ceil

from discord.ext import commands
from cogs import leaderboard


class Inventory(commands.Cog):
    version = '0.1'
    EMOJIS = {
        "0":              "0️⃣",
        "1":              "1️⃣",
        "2":              "2️⃣",
        "3":              "3️⃣",
        "4":              "4️⃣",
        "5":              "5️⃣",
        "6":              "6️⃣",
        "7":              "7️⃣"}

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='inventory', help='displays your inventory', aliases=["inv"])
    async def inv(self, ctx):
        if ctx.guild.id == 689877729294024725:
            return await self.inventorymenu(ctx)
        elif ctx.guild.id == 502944697225052181:
            return await self.inventorymenu(ctx, mode='anime')
        else:
            return await self.inventorymainmenu(ctx)

    async def inventorymainmenu(self, ctx):
        embed = discord.Embed(title='Inventory Menu',
                              description='Please react with a number based on which inventory you would like to see\nReact with :zero: for your regular inventory\nReact with :one: for your anime inventory\nOr wait 60s to cancel',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        m = await ctx.send(embed=embed)

        await m.add_reaction(self.EMOJIS["0"])
        await m.add_reaction(self.EMOJIS["1"])

        def check(r, u):
            if r.message == m and u == ctx.author:
                return r, u

        while True:
            try:
                r, u = await self.bot.wait_for('reaction_add', check=check, timeout=60)
                if r.emoji == self.EMOJIS["0"]:
                    await m.clear_reactions()
                    return await self.inventorymenu(ctx, m=m)
                elif r.emoji == self.EMOJIS["1"]:
                    await m.clear_reactions()
                    return await self.inventorymenu(ctx, m, 'anime')
            except asyncio.TimeoutError:
                return await m.delete()

    async def inventorymenu(self, ctx, m=None, mode=None):

        embed = discord.Embed(title='Inventory Menu',
                              description='Loading...',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        if m is None:
            m = await ctx.send(embed=embed)
        else:
            await m.edit(embed=embed)

        for e in self.EMOJIS.values():
            if mode is not None:
                if e == self.EMOJIS["4"]:
                    break
            await m.add_reaction(e)

        basedesc = 'Please react with a number based on how you would like your inventory sorted\nReact with :zero: for pick up order: **oldest - newest**\n React with :one: for pick up order: **newest - oldest**\nReact with :two: for by alphabetical: **A - Z**\nReact with :three: for by alphabetical: **Z - A**\n'
        if mode is None:
            basedesc += 'React with :four: for quantity: **high - low**\nReact with :five: for quantity: **low - high**\nReact with :six: for rarity: **high - low**\nReact with :seven: for rarity: **low - high**\n'
        basedesc += 'Or wait 60s to cancel'

        embed = discord.Embed(title='Inventory Menu',
                              description=basedesc,
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        await m.edit(embed=embed)

        def check(r, u):
            if r.message == m and u == ctx.author:
                return r, u

        while True:
            try:
                r, u = await self.bot.wait_for('reaction_add', check=check, timeout=60)
                if r.emoji == self.EMOJIS["0"]:
                    await m.clear_reactions()
                    if mode is None:
                        return await self.inventory(ctx, m, "time o")
                    else:
                        return await self.animeinventory(ctx, m, "time o")
                elif r.emoji == self.EMOJIS["1"]:
                    await m.clear_reactions()
                    if mode is None:
                        return await self.inventory(ctx, m, "time m")
                    else:
                        return await self.animeinventory(ctx, m, "time n")
                elif r.emoji == self.EMOJIS["2"]:
                    await m.clear_reactions()
                    if mode is None:
                        return await self.inventory(ctx, m, "alphabet a")
                    else:
                        return await self.animeinventory(ctx, m, "alphabet a")
                elif r.emoji == self.EMOJIS["3"]:
                    await m.clear_reactions()
                    if mode is None:
                        return await self.inventory(ctx, m, "alphabet z")
                    else:
                        return await self.animeinventory(ctx, m, "alphabet z")
                elif r.emoji == self.EMOJIS["4"]:
                    await m.clear_reactions()
                    return await self.inventory(ctx, m, "quantity h")
                elif r.emoji == self.EMOJIS["5"]:
                    await m.clear_reactions()
                    return await self.inventory(ctx, m, "quantity l")
                elif r.emoji == self.EMOJIS["6"]:
                    await m.clear_reactions()
                    return await self.inventory(ctx, m, "rarity h")
                elif r.emoji == self.EMOJIS["7"]:
                    await m.clear_reactions()
                    return await self.inventory(ctx, m, "rarity l")
                else:
                    await r.remove(u)
            except asyncio.TimeoutError:
                await ctx.message.delete()
                await m.delete()
                return None, None

    async def inventory(self, ctx, m, mode=None):
        with open(f'cogs/leaderboards/lb{ctx.guild.id}.json', 'r') as file:
            d = json.loads(file.read())
        if await leaderboard.Leaderboard.checkuser(self, ctx.message.author.id, d):
            for user in d['users']:
                if user['userid'] == ctx.message.author.id:
                    fullinv = await self.sortinv(mode, user['images'])
                    inv = ''
                    if len(user['images']) <= 10:
                        for i, item in enumerate(fullinv, start=1):
                            inv += f'{i}.\U00002800 {item["count"]}x **{item["name"]}** \n'
                        embed = discord.Embed(colour=ctx.guild.get_member(self.bot.user.id).colour)
                        embed.title = 'your inventory'
                        embed.description = inv
                        embed.set_thumbnail(url=ctx.message.author.avatar_url_as())
                        await m.edit(embed=embed)
                        await asyncio.sleep(100)
                        await ctx.message.delete()
                        return await m.delete()
                    else:
                        if len(user['images']) >= 200:
                            perpage = 20
                        else:
                            perpage = 10
                        temp = 0
                        f_embed = discord.Embed(colour=ctx.guild.get_member(self.bot.user.id).colour)
                        f_embed.title = 'your inventory'
                        f_embed.set_thumbnail(url=ctx.message.author.avatar_url_as())
                        await m.edit(embed=f_embed)
                        while True:
                            if temp == len(user['images']):
                                temp -= (temp % perpage)
                            inventory = ''
                            for i in range(temp, len(user['images'])):
                                inventory += f'{i+1}.\U00002800 {fullinv[i]["count"]}x **{fullinv[i]["name"]}**\n'
                                temp += 1
                                if (i + 1) % perpage == 0:
                                    temp = i + 1
                                    break
                            embed = f_embed
                            embed.description = inventory
                            embed.set_footer(text='page {0}/{1}'.format(ceil(temp/perpage), ceil(len(user['images'])/perpage)))
                            await m.edit(embed=embed)
                            await m.add_reaction('\U00002B05')
                            await m.add_reaction('\U000027A1')
                            while True:
                                def check(r, u):
                                    if r.message == m and u == ctx.message.author:
                                        return r, u
                                try:
                                    r, u = await self.bot.wait_for('reaction_add', check=check, timeout=60)
                                except asyncio.TimeoutError:
                                    await ctx.message.delete()
                                    return await m.delete()
                                if str(r.emoji) == '\U00002B05':
                                    if temp == perpage - 1:
                                        pass
                                    else:
                                        if temp < perpage * 2:
                                            temp = 0
                                        else:
                                            if temp % perpage == 0:
                                                temp -= perpage * 2
                                            else:
                                                temp -= perpage + (temp % perpage)
                                    await r.remove(ctx.message.author)
                                    break
                                if str(r.emoji) == '\U000027A1':
                                    await r.remove(ctx.message.author)
                                    break
        if m is not None:
            await m.delete()
        return await ctx.send(f"{ctx.message.author.mention}, you don't have anything in your inventory")

    async def sortinv(self, mode, inv):
        if mode == "time o":
            return inv
        elif mode == "time n":
            inv.reverse()
            return inv
        elif mode == "alphabet a":
            inv.sort(key=operator.itemgetter('name'))
            return inv
        elif mode == "alphabet z":
            inv.sort(key=operator.itemgetter('name'), reverse=True)
            return inv
        elif mode == "quantity h":
            inv.sort(key=operator.itemgetter('count'), reverse=True)
            return inv
        elif mode == "quantity l":
            inv.sort(key=operator.itemgetter('count'))
            return inv
        elif mode == "rarity h":
            inv = await self.sortrarity(inv, False)
            return inv
        elif mode == "rarity l":
            inv = await self.sortrarity(inv, True)
            return inv
        else:
            return inv

    async def sortrarity(self, inv, reverse):
        with open(f'cogs/flowers.json', 'r') as file:
            f = json.loads(file.read())
        f = await self.reversedict(f)
        temp = []
        if not reverse:
            f.reverse()
        for cat in f:
            for flower in cat:
                n = list(flower.keys())
                for item in inv:
                    if n[0] == item['name']:
                        temp.append(item)
        for item in inv:
            if not temp.count(item):
                if not reverse:
                    temp.append(item)
                else:
                    temp.insert(0, item)
        return temp

    async def reversedict(self, dict):
        temp = []
        for key in dict:
            temp.append(dict[key])
        return temp

    async def animeinventory(self, ctx, m, mode=None):
        with open(f'cogs/leaderboards/a{ctx.guild.id}.json', 'r') as file:
            d = json.loads(file.read())
        owner = ctx.message.author
        c = await leaderboard.Leaderboard.checkuser(self, owner.id, d)
        if c:
            for user in d['users']:
                if owner.id == user['userid']:
                    fullinv = await self.sortinv(mode, user['images'])
                    inv = ''
                    if len(user['images']) < 10:
                        for i, item in enumerate(fullinv):
                            inv += f'{i+1}. **{item["name"]}**\n'
                        embed = discord.Embed(colour=ctx.guild.get_member(self.bot.user.id).colour)
                        embed.title = 'your inventory'
                        embed.description = inv
                        embed.set_thumbnail(url=owner.avatar_url_as())
                        await m.edit(embed=embed)
                        await asyncio.sleep(100)
                        await ctx.message.delete()
                        return await m.delete()
                    else:
                        if len(user['images']) >= 200:
                            perpage = 20
                        else:
                            perpage = 10
                        temp = 0
                        f_embed = discord.Embed(colour=ctx.guild.get_member(self.bot.user.id).colour)
                        f_embed.title = 'your inventory'
                        f_embed.set_thumbnail(url=owner.avatar_url_as())
                        await m.edit(embed=f_embed)
                        while True:
                            if temp == len(user['images']):
                                temp -= (temp % perpage)
                            inventory = ''
                            for item in range(temp, len(fullinv)):
                                inventory += f'{item+1}. **{fullinv[item]["name"]}**\n'
                                temp += 1
                                if (item + 1) % perpage == 0:
                                    temp = item + 1
                                    break
                            embed = f_embed
                            embed.description = inventory
                            embed.set_footer(text='page {0}/{1}'.format(ceil(temp/perpage), ceil(len(fullinv)/perpage)))
                            await m.edit(embed=embed)
                            await m.add_reaction('\U00002B05')
                            await m.add_reaction('\U000027A1')
                            while True:
                                def check(r, u):
                                    if r.message == m and u == ctx.message.author:
                                        return r, u
                                try:
                                    r, u = await self.bot.wait_for('reaction_add', check=check, timeout=60)
                                except asyncio.TimeoutError:
                                    await ctx.message.delete()
                                    return await m.delete()
                                if str(r.emoji) == '\U00002B05':
                                    if temp == perpage - 1:
                                        pass
                                    else:
                                        if temp < perpage * 2:
                                            temp = 0
                                        else:
                                            if temp % perpage == 0:
                                                temp -= perpage * 2
                                            else:
                                                temp -= perpage + (temp % perpage)
                                    await r.remove(ctx.message.author)
                                    break
                                if str(r.emoji) == '\U000027A1':
                                    await r.remove(ctx.message.author)
                                    break
        if m is not None:
            await m.delete()
        return await ctx.send(f"{ctx.message.author.mention}, you don't have anything in your anime inventory")

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
                if await leaderboard.Leaderboard.checkimage(self, u['userid'], ctx.guild.id, image):
                    msg = await ctx.send(f'{user.mention}! {um} wants to give you {image}, do you accept? '
                                         '[(y)es/(n)o]')
                    def check(m):
                        return m.channel == ctx.channel and m.author == user

                    try:
                        while True:
                            m = await self.bot.wait_for('message', check=check, timeout=60)
                            if m.content.lower() in ['y', 'yes']:
                                await self.transferimage(ctx.message.author.id, user.id, image, sid)
                                return await msg.edit(content=f'congratulations {user.mention}, you\'re the proud new owner of {image}')
                            if m.content.lower() in ['n', 'no']:
                                return await msg.edit(content=f'uh oh, {user.mention} doesn\'t want {um}\'s {image}')
                    except asyncio.TimeoutError:
                        return await msg.edit(content=f'uh oh, {user.mention} didn\'t respond in time, please try again when they\'re not busy')
                else:
                    return await self.animegive(ctx, user=user, image=image)
        return await self.animegive(ctx, user, image=image)

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
                if leaderboard.AnimeLeaderboard.checkimage(self, ctx.author.id, ctx.guild.id, image):
                    msg = await ctx.send(f'{user.mention}! {um} wants to give you {image}, do you accept? '
                                         '[(y)es/(n)o]')
                    def check(m):
                        return m.channel == ctx.channel and m.author == user

                    try:
                        while True:
                            m = await self.bot.wait_for('message', check=check, timeout=60)
                            if m.content.lower() in ['y', 'yes']:
                                if leaderboard.AnimeLeaderboard.checkimage(self, user.id, ctx.guild.id, image):
                                    return await msg.edit(content=f'{user.mention} already has this character!')
                                else:
                                    await self.atransferimage(ctx.message.author.id, user.id, image, sid)
                                    return await msg.edit(content=f'congratulations {user.mention}, you\'re the proud new owner of {image}')
                            if m.content.lower() in ['n', 'no']:
                                await msg.edit(content=f'uh oh, {user.mention} doesn\'t want {um}\'s {image}')
                                return
                    except asyncio.TimeoutError as e:
                        return await msg.edit(content=f'uh oh, {user.mention} didn\'t respond in time, please try again when they\'re not busy')
                else:
                    return await ctx.send(f'you don\'t have any {image}s to give out!')
        return await ctx.send('you don\'t have anything to give out! please try collecting some items first')

    @commands.command(name='trade')
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def trade(self, ctx, user: discord.Member):
        u = ctx.message.author
        offer0 = []
        offer1 = []

        if user == self.bot.user:
            return await ctx.send('thank you but i have no worldly desires, other than sunlight of course')
        elif user == u:
            return await ctx.send('you can\'t trade with yourself')

        temp = await ctx.send(f'{user.mention}! {u.mention} wants to trade with you, are you available? [(y)es/(n)o]')

        def check(m):
            return m.channel == ctx.channel and m.author == user
        try:
            while True:
                m = await self.bot.wait_for('message', check=check, timeout=60)
                if m.content.lower() in ['y', 'yes']:
                    await temp.delete()
                    await m.delete()
                    temp = await ctx.send(f'{u.mention} it\'s your turn to make an offer')
                    offer0 = await self.tradeloop(ctx, u, user)
                    await temp.delete()
                    break
                elif m.content.lower() in ['n', 'no']:
                    return await ctx.send(f'sorry {u.mention}, looks like {user.mention} doesn\'t want to trade right now')
                else:
                    return await ctx.send('I\'m sorry I didn\'t understand that, please answer [(y)es/(n)o]')
        except asyncio.TimeoutError:
            return await ctx.send(f'uh oh, {user.mention} didn\'t respond in time, please try again when they\'re not busy')

        if not offer0:
            return await ctx.send(f'uh oh, looks like {u.mention} didn\'t make an offer')

        embed = discord.Embed(title=f'{u.display_name}\'s offer',
                              description='\n'.join([character for character in offer0]),
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        embed.set_thumbnail(url=u.avatar_url_as())

        menu = await ctx.send(embed=embed)
        temp = await ctx.send(f'{user.mention}, this is {u.mention}\'s offer, do you accept? [(y)es/(n)o]')
        try:
            while True:
                m = await self.bot.wait_for('message', check=check, timeout=60)
                if m.content.lower() in ['y', 'yes']:
                    await menu.delete()
                    await temp.delete()
                    temp0 = await ctx.send(f'{user.mention} it\'s your turn to make an offer')
                    offer1 = await self.tradeloop(ctx, user, u)
                    await temp0.delete()
                    break
                elif m.content.lower() in ['n', 'no']:
                    await menu.delete()
                    await temp.delete()
                    return await ctx.send(f'sorry {u.mention}, looks like {user.mention} doesn\'t like your trade offer')
                else:
                    await ctx.send('I\'m sorry I didn\'t understand that, please answer [(y)es/(n)o]')
        except asyncio.TimeoutError:
            await temp.delete()
            await menu.delete()
            return await ctx.send(f'uh oh, {user.mention} didn\'t respond in time, please try again when they\'re not busy')

        if not offer1:
            return await ctx.send(f'uh oh, looks like {user.mention} didn\'t make an offer')

        temp0 = await ctx.send(f'{u.mention}, this is {user.mention}\'s offer, do you accept? [(y)es/(n)o]')
        embed = discord.Embed(title='Final trade', colour=ctx.guild.get_member(self.bot.user.id).colour)
        embed.add_field(name=f'{u.display_name}\'s trade', value='\n'.join([character for character in offer0]))
        embed.add_field(name=f'{user.display_name}\'s trade', value='\n'.join([character for character in offer1]))
        menu = await ctx.send(embed=embed)

        def check(m):
            return m.channel == ctx.channel and m.author == u
        try:
            while True:
                m = await self.bot.wait_for('message', check=check, timeout=60)
                if m.content.lower() in ['y', 'yes']:
                    await m.delete()
                    await temp0.delete()
                    break
                elif m.content.lower() in ['n', 'no']:
                    await m.delete()
                    await temp0.delete()
                    return await ctx.send(f'sorry {u.mention}, looks like {user.mention} doesn\'t like your trade offer')
                elif m.content.lower() in ['.animeinventory', '.ainv', '.aniinv']:
                    pass
                else:
                    await m.delete()
                    await temp0.delete()
                    await ctx.send('I\'m sorry I didn\'t understand that, please answer [(y)es/(n)o]')
        except asyncio.TimeoutError:
            await temp0.delete()
            return await ctx.send(f'uh oh, {user.mention} didn\'t respond in time, please try again when they\'re not busy')

        for character in offer0:
            await self.atransferimage(u.id, user.id, character, ctx.guild.id)
        for character in offer1:
            await self.atransferimage(user.id, u.id, character, ctx.guild.id)

        return await ctx.send('Trade complete!')

    async def tradeloop(self, ctx, user_from, user_to):
        with open(f'cogs/leaderboards/a{ctx.guild.id}.json', 'r') as file:
            d = json.loads(file.read())

        def check(m):
            return m.channel == ctx.channel and m.author == user_from

        embed = discord.Embed(title='Trading', colour=ctx.guild.get_member(self.bot.user.id).colour)
        embed.add_field(name=f'{user_from.display_name}\'s offer', value='\U0000200B')
        embed.set_thumbnail(url=user_from.avatar_url_as())

        menu = await ctx.send(embed=embed)

        remaininginv = []
        offer = []

        for u in d['users']:
            if u['userid'] == user_from.id:
                for image in u['images']:
                    remaininginv.append(image['name'].lower())

        while True:
            if not remaininginv:
                await ctx.send('you have nothing left to trade!')
                return offer

            msg = await ctx.send(f'{user_from.mention}! Please offer a character to trade')
            while True:
                try:
                    m = await self.bot.wait_for('message', check=check, timeout=90)
                    badcharacter = None
                    if leaderboard.AnimeLeaderboard.checkimage(self, user_from.id, ctx.guild.id, m.content):
                        await msg.delete()
                        await m.delete()
                        if leaderboard.AnimeLeaderboard.checkimage(self, user_to.id, ctx.guild.id, m.content):
                            badcharacter = await ctx.send(f'{user_to.mention} already has this character! Please offer a different character')
                        else:
                            offer.append(m.content)
                            remaininginv.remove(m.content.lower())
                        if not offer:
                            temp = '\U0000200B'
                        else:
                            temp = '\n'.join([character for character in offer])
                        embed = discord.Embed(title='Trading', colour=ctx.guild.get_member(self.bot.user.id).colour)
                        embed.add_field(name=f'{user_from.display_name}\'s offer', value=temp)
                        embed.set_thumbnail(url=user_from.avatar_url_as())

                        await menu.edit(embed=embed)
                        break
                    else:
                        await m.delete()
                        await ctx.send('I couldn\'t find that character, please try again')
                except asyncio.TimeoutError:
                    await menu.delete()
                    await ctx.send('uh oh, please try making an offer')
                    return offer

            msg = await ctx.send(f'{user_from.mention}, would you like to offer another character? [(y)es/(n)o]')
            while True:
                try:

                    m = await self.bot.wait_for('message', check=check, timeout=60)
                    if badcharacter:
                        await badcharacter.delete()
                    await msg.delete()
                    await m.delete()
                    if m.content.lower() in ['y', 'yes']:
                        break
                    elif m.content.lower() in ['n', 'no']:
                        await menu.delete()
                        return offer
                    else:
                        await menu.delete()
                        await ctx.send('I couldn\'t understand that, I will be using your current offer')
                        return offer
                except asyncio.TimeoutError:
                    await menu.delete()
                    await ctx.send('uh oh, we ran out of time, I will be using your current offer')
                    return offer

    async def transferimage(self, id_from, id_to, image, sid):
        with open(f'cogs/leaderboards/lb{sid}.json', 'r') as file:
            d = json.loads(file.read())
        for i, user in enumerate(d['users']):
            if user['userid'] == id_from:
                for im in user['images']:
                    if im["name"].lower() == image.lower():
                        temp = im["name"]
                        if im["count"]-1:
                            im.update({"count": im["count"]-1})
                        else:
                            user["images"].remove(im)
                        break
                break
        with open(f'cogs/leaderboards/lb{sid}.json', 'w') as file:
            json.dump(d, file)
        await leaderboard.Leaderboard.addpoint(self, id_to, sid, temp, 0)

    async def atransferimage(self, id_from, id_to, imagename, sid):
        with open(f'cogs/leaderboards/a{sid}.json', 'r') as file:
            d = json.loads(file.read())
        temp = None
        for user in d['users']:
            if user['userid'] == id_from:
                for character in user['images']:
                    if character['name'].lower() == imagename.lower():
                        temp = character
                        user['images'].remove(character)
                        break
                break
        with open(f'cogs/leaderboards/a{sid}.json', 'w') as file:
            json.dump(d, file)
        await leaderboard.AnimeLeaderboard.addpoint(self, id_to, sid, temp['url'], temp['name'], 0)

    @give.error
    async def giveerror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
            await ctx.send("please format as `.give [user] [item]`")

    @trade.error
    async def eventerror(self, ctx, error):
        if isinstance(error, commands.MaxConcurrencyReached):
            await ctx.send('Only one trade can occur per channel, please wait until the previous trade is complete to begin yours')

def setup(bot):
    bot.add_cog(Inventory(bot))



