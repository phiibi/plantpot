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

    @commands.command(name='inventory', help='displays your inventory', aliases = ["inv"])
    async def inventory(self, ctx, mode: str = None):
        sid = ctx.guild.id
        with open(f'cogs/leaderboards/lb{sid}.json', 'r') as file:
            d = json.loads(file.read())
        c = await leaderboard.Leaderboard.checkuser(self, ctx.message.author.id, d)
        if c:
            for user in d['users']:
                if user['userid'] == ctx.message.author.id:
                    inv = ''
                    if len(user['images']) <= 10:
                        for i, kv in enumerate(user['images'], start=1):
                            for k, v in kv.items():
                                inv += f'{i}.\U00002800 {v}x **{k}** \n'
                        embed = discord.Embed()
                        embed.title = 'your inventory'
                        embed.description = inv
                        embed.set_thumbnail(url=ctx.message.author.avatar_url_as())
                        m = await ctx.send(embed=embed)
                        await asyncio.sleep(120)
                        return await m.delete()
                    else:
                        if len(user['images']) >= 200:
                            perpage = 20
                        else:
                            perpage = 10
                        start = time.time()
                        temp = 0
                        f_embed = discord.Embed()
                        f_embed.title = 'your inventory'
                        f_embed.set_thumbnail(url=ctx.message.author.avatar_url_as())
                        m = await ctx.send(embed=f_embed)
                        while True:
                            if temp == len(user['images']):
                                temp -= (temp % perpage)
                            inv = ''
                            for i in range(temp, len(user['images'])):
                                for k, v in user['images'][i].items():
                                    inv += f'{i+1}. \U00002800 {v}x **{k}**\n'
                                temp += 1
                                if (i + 1) % perpage == 0:
                                    temp = i + 1
                                    break
                            embed = f_embed
                            embed.description = inv
                            embed.set_footer(text='page {0}/{1}'.format(ceil(temp/perpage), ceil(len(user['images'])/perpage)))
                            await m.edit(embed=embed)
                            await m.add_reaction('\U00002B05')
                            await m.add_reaction('\U000027A1')
                            while True:
                                if time.time() - start > 120:
                                    return await m.delete()
                                m = await m.channel.fetch_message(m.id)
                                if m.reactions[0].count > 1:
                                    async for u in m.reactions[0].users():
                                        if u == ctx.message.author:
                                            if temp == perpage - 1:
                                                pass
                                            else:
                                                if temp < perpage * 2:
                                                    temp = 0
                                                elif temp % perpage == 0:
                                                    temp -= perpage * 2
                                                else:
                                                    temp -= perpage + (temp % perpage)
                                                break
                                    await m.reactions[0].remove(ctx.message.author)
                                    break
                                if m.reactions[1].count > 1:
                                    async for u in m.reactions[1].users():
                                        if u == ctx.message.author:
                                            break
                                    await m.reactions[1].remove(ctx.message.author)
                                    break

    @commands.command(name='animeinventory', help='displays inventory', aliases = ["aniinv", "ainv", "anime inventory"])
    async def animeinventory(self, ctx, owner: discord.Member = None):
        sid = ctx.guild.id
        with open(f'cogs/leaderboards/a{sid}.json', 'r') as file:
            d = json.loads(file.read())
        if owner is None:
            owner = ctx.message.author
        c = await leaderboard.Leaderboard.checkuser(self, owner.id, d)
        if c:
            for user in d['users']:
                if owner.id == user['userid']:
                    inventory = ''
                    if len(user['image_name']) < 10:
                        for item in range(0, len(user['image_name'])):
                            inventory += '{0}. **'.format(item+1) + user['image_name'][item] + '**\n'
                        embed = discord.Embed()
                        embed.title = 'your inventory'
                        embed.description = inventory
                        embed.set_thumbnail(url=owner.avatar_url_as())
                        m = await ctx.send(embed=embed)
                        await asyncio.sleep(120)
                        return await m.delete()
                    else:
                        if len(user['image_name']) >= 200:
                            perpage = 20
                        else:
                            perpage = 10
                        start = time.time()
                        temp = 0
                        f_embed = discord.Embed()
                        f_embed.title = 'your inventory'
                        f_embed.set_thumbnail(url=owner.avatar_url_as())
                        m = await ctx.send(embed=f_embed)
                        while True:
                            if temp == len(user['image_name']):
                                temp -= (temp % perpage)
                            inventory = ''
                            for item in range(temp, len(user['image_name'])):
                                inventory += f'{item+1}. **' + user['image_name'][item] + '**\n'
                                temp += 1
                                if (item + 1) % perpage == 0:
                                    temp = item + 1
                                    break
                            embed = f_embed
                            embed.description = inventory
                            embed.set_footer(text='page {0}/{1}'.format(ceil(temp/perpage), ceil(len(user['image_name'])/perpage)))
                            await m.edit(embed=embed)
                            await m.add_reaction('\U00002B05')
                            await m.add_reaction('\U000027A1')
                            while True:
                                if time.time() - start > 120:
                                    return await m.delete()
                                m = await m.channel.fetch_message(m.id)
                                if m.reactions[0].count > 1:
                                    async for u in m.reactions[0].users():
                                        if u == owner:
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
                                                break
                                    await m.reactions[0].remove(owner)
                                    break
                                if m.reactions[1].count > 1:
                                    async for u in m.reactions[1].users():
                                        if u == owner:
                                            break
                                    await m.reactions[1].remove(owner)
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
                if await leaderboard.Leaderboard.checkimage(self, u['userid'], ctx.guild.id, image):
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
                    return await ctx.send(f'you don\'t have {image}s to give out')
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
                        while True:
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

    @commands.command(name='trade')
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
                    offer0 = await self.tradeloop(ctx, u)
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
                              description='\n'.join([character for character in offer0]))
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
                    offer1 = await self.tradeloop(ctx, user,)
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

        embed = discord.Embed(title=f'{user.display_name}\'s offer',
                              description='\n'.join([character for character in offer0]))

        temp0 = await ctx.send(f'{u.mention}, this is {user.mention}\'s offer, do you accept? [(y)es/(n)o]')
        embed = discord.Embed(title='Final trade')
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
                elif m.content.lower() == '.animeinventory':
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

    async def tradeloop(self, ctx, user):
        with open(f'cogs/leaderboards/a{ctx.guild.id}.json', 'r') as file:
            d = json.loads(file.read())

        def check(m):
            return m.channel == ctx.channel and m.author == user

        embed = discord.Embed(title='Trading')
        embed.add_field(name=f'{user.display_name}\'s offer', value='\U0000200B')
        embed.set_thumbnail(url=user.avatar_url_as())

        menu = await ctx.send(embed=embed)

        remaininginv = []
        offer = []

        for u in d['users']:
            if u['userid'] == user.id:
                remaininginv = u['image_name']

        while True:
            if not remaininginv:
                await ctx.send('you have nothing left to trade!')
                return offer

            msg = await ctx.send(f'{user.mention}! Please offer a character to trade')
            try:
                while True:
                    m = await self.bot.wait_for('message', check=check, timeout=90)
                    if leaderboard.AnimeLeaderboard.checkimage(self, user.id, ctx.guild.id, m.content):
                        await msg.delete()
                        await m.delete()
                        offer.append(m.content)
                        remaininginv.remove(m.content)

                        embed = discord.Embed(title='Trading')
                        embed.add_field(name=f'{user.display_name}\'s offer', value='\n'.join([character for character in offer]))
                        embed.set_thumbnail(url=user.avatar_url_as())

                        await menu.edit(embed=embed)
                        break
                    else:
                        await m.delete()
                        await ctx.send('I couldn\'t find that character, please try again')
            except asyncio.TimeoutError:
                await menu.delete()
                await ctx.send('uh oh, please try making an offer')
                return offer

            msg = await ctx.send(f'{user.mention}, would you like to offer another character? [(y)es/(n)o]')
            try:
                while True:
                    m = await self.bot.wait_for('message', check=check, timeout=60)
                    if m.content.lower() in ['y', 'yes']:
                        await m.delete()
                        await msg.delete()
                        break
                    elif m.content.lower() in ['n', 'no']:
                        await msg.delete()
                        await m.delete()
                        await menu.delete()
                        return offer
                    else:
                        await m.delete()
                        await msg.delete()
                        await menu.delete()
                        await ctx.send('I couldn\'t understand that, I will be using your current offer')
                        return offer
            except asyncio.TimeoutError:
                await menu.delete()
                await ctx.send('uh oh, we ran out of time, I will be using your current offer')
                return offer

    async def transferimage(self, id_from, id_to, image, sid):
        await leaderboard.Leaderboard.addpoint(self, id_to, sid, image, 0)
        with open(f'cogs/leaderboards/lb{sid}.json', 'r') as file:
            d = json.loads(file.read())
        for i, user in enumerate(d['users']):
            if user['userid'] == id_from:
                for im in user['images']:
                    for k in im.items():
                        if k[0] == image:
                            if im.get(image) == 1:
                                user['images'].remove(im)
                            else:
                                im.update({f'{image}': im.get(image)-1})
                break
        with open(f'cogs/leaderboards/lb{sid}.json', 'w') as file:
            json.dump(d, file)

    async def atransferimage(self, id_from, id_to, imagename, sid):
        with open(f'cogs/leaderboards/a{sid}.json', 'r') as file:
            d = json.loads(file.read())
        tempname = ""
        tempurl = ""
        for i, user in enumerate(d['users']):
            if user['userid'] == id_from:
                n = user['image_name'].index(imagename)
                image_n = user['image_name']
                image_u = user['image_url']
                tempname = image_n[n]
                tempurl = image_u[n]
                image_n.remove(imagename)
                image_u.pop(n)
                d['users'][i].update({"userid": id_from,
                                      "points": user['points'],
                                      "image_name": image_n})
                break
        with open(f'cogs/leaderboards/a{sid}.json', 'w') as file:
            json.dump(d, file)
        await leaderboard.AnimeLeaderboard.addpoint(self, id_to, sid, tempurl, tempname, 0)

    @commands.command(name='hh', hidden=True)
    async def getpoints(self, image):
        hadbefore = True
        points = {"Ultra Special Amazing": 500,
                  "Legendary": 300,
                  "Mythic": 200,
                  "Epic": 100,
                  "Plant\'s Favourites": 50,
                  "Ultra Rare": 25,
                  "Rare": 10,
                  "Uncommon": 5,
                  "Common": 1}
        points_collected = {"Ultra Special Amazing": 200,
                            "Legendary": 100,
                            "Mythic": 60,
                            "Epic": 30,
                            "Plant\'s Favourites": 20,
                            "Ultra Rare": 10,
                            "Rare": 5,
                            "Uncommon": 2,
                            "Common": 1}
        with open(f'cogs/flowers.json', 'r') as file:
            f = json.loads(file.read())
        for cat in f:
            for flower in f[cat]:
                t = list(flower.items())
                if t[0][0] == image:
                    if hadbefore:
                        print(points_collected.get(cat))
                        return points_collected.get(cat)
                    else:
                        print(points.get(cat))
                        return points.get(cat)

    @give.error
    async def giveerror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
            await ctx.send("please format as `.give [user] [item]`")

    @animegive.error
    async def animegiveerror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
            await ctx.send("please format as `.animegive [user] [character]`")

def setup(bot):
    bot.add_cog(Inventory(bot))



