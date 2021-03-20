#badges.py

import discord
import json
import time

from discord.ext import commands
from cogs import leaderboard, checkers
from math import ceil

class Badge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='badge')
    async def badge(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @badge.command(name='inventory')
    async def inventory(self, ctx):
        with open(f'cogs/badges.json', 'r') as file:
            d = json.loads(file.read())
        if await leaderboard.Leaderboard.checkuser(self, ctx.message.author.id, d):
            for user in d['users']:
                if ctx.message.author.id == user['userid']:
                    inventory = ''
                    if len(user['badges']) < 10:
                        for item in range(0, len(user['badges'])):
                            for i in user['badges'][item]:
                                tempstr = i + "  " + user['badges'][item][i]
                            inventory += '{0}. **'.format(item+1) + tempstr + '**\n'
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
                            if temp == len(user['badges']):
                                temp -= (temp % 10)
                            inventory = ''
                            for item in range(temp, len(user['badges'])):
                                inventory += f'{item+1}. **' + user['badges'][item] + '**\n'
                                temp += 1
                                if (item + 1) % 10 == 0:
                                    temp = item + 1
                                    break
                            embed = f_embed
                            embed.description = inventory
                            embed.set_footer(text='page {0}/{1}'.format(ceil(temp/10), ceil(len(user['badges'])/10)))
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

    @badge.command(name='make', hidden=True)
    @checkers.is_plant_owner()
    async def make(self, ctx, *, name):
        with open('cogs/badges.json', 'r') as file:
            d = json.loads(file.read())
        if d['badges'].get(name):
            return await ctx.send('this badge already exists!')
        else:
            await ctx.send('please enter the emoji you would like to use')

            def check(m):
                return m.channel == ctx.channel and m.author == ctx.message.author

            m = await self.bot.wait_for('message', check=check)
            d['badges'].update({name: m.content})
            with open('cogs/badges.json', 'w') as file:
                json.dump(d, file)

    @badge.command(name='give', hidden=True)
    @checkers.is_plant_owner()
    async def give(self, ctx, user: discord.Member, *, name):
        with open('cogs/badges.json', 'r') as file:
            d = json.loads(file.read())
        await Badge.adduser(self, ctx, d)
        temp = d['badges'].get(name)
        if not temp:
            return await ctx.send('I couldn\'t find that badge...')
        else:
            for i, n in enumerate(d['users']):
                if n['userid'] == ctx.message.author.id:
                    if await Badge.checkbadge(self, ctx, name, d):
                        return await ctx.send('this user already has that badge!')
                    else:
                        n['badges'].append({name: temp})
                        await ctx.send('{0} just got {1} {2}!'.format(user.mention, name, temp))
        with open('cogs/badges.json', 'w') as file:
            json.dump(d, file)

    async def adduser(self, ctx, d):
        u = await leaderboard.Leaderboard.checkuser(self, ctx.message.author.id, d)
        if not u:
            u = {"userid": ctx.message.author.id,
                  "badges": []}
            d['users'].append(u)
            with open('cogs/badges.json', 'w') as file:
                json.dump(d, file)

    async def checkbadge(self, ctx, badge, d):
        for u in d['users']:
            if u['userid'] == ctx.message.author.id:
                for i in u['badges']:
                    for n in i:
                        if n == badge:
                            return True
        return False

    async def getbadge(self, badge):
        with open('cogs/badges.json', 'r') as file:
            d = json.loads(file.read())
        return d['badges'].get(badge)



def setup(bot):
    bot.add_cog(Badge(bot))
