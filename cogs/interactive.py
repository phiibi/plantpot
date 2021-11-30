# interactive.py
# cog for fun things

import discord
import random
import json

from discord.ext import commands
from cogs import leaderboard


class Interactive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='avatar', help='returns my avatar')
    async def avatar(self, ctx):
        embed = discord.Embed(colour=ctx.guild.get_member(self.bot.user.id).colour)
        embed.title = 'here\'s my avatar!'
        embed.set_image(url='https://i.imgur.com/I9SPukW.jpg')
        embed.set_footer(text='art done by https://twitter.com/bunnabells')
        await ctx.send(embed=embed)

    @commands.command(name='ping', help='pong')
    async def ping(self, ctx):
        replies = ['please water me daily!',
                   'stay in a good mood, everyday!',
                   'photosynthesis in progress...',
                   'this dirt tastes... dirt-y',
                   'I\'m unbeleafable',
                   'babibabi boom!',
                   'how is potting plants going?',
                   'leaves and petals are the two greatest inventions!',
                   'beep boop',
                   'pollination commencing...',
                   'I need sunlight to photosynthesise, you just need to get out more']
        await ctx.send(random.choice(replies))

    @commands.command(name='ohno', help='oh no!', hidden=True)
    async def ohno(self, ctx):
        embed = discord.Embed()
        embed.title = 'you fool!'
        embed.set_image(url='https://i.imgur.com/ZiwFFNJ.png')
        await ctx.send(embed=embed)

    @commands.command(name='progression', help='check event progress')
    async def progression(self, ctx, *, event: str):
        if event == 'spring':
            await self.getspringprogress(ctx, ctx.message.author)
        if event == 'anime' and ctx.guild.id == 813532137050341407:
            await self.getanimeprogress(ctx, ctx.message.author)

    async def getspringprogress(self, ctx, user):
        with open(f'cogs/leaderboards/lb{ctx.guild.id}.json', 'r') as file:
            d = json.loads(file.read())

        f = await self.getflowernames()
        count = 0
        for u in d['users']:
            if u['userid'] == user.id:
                for item in u['images']:
                    if f.count(item['name']) == 1:
                        count += 1
                    if item['name'] == 'Coneflower' or item['name'] == 'Amaryllis':
                        count += 1
        embed = discord.Embed(colour=ctx.guild.get_member(self.bot.user.id).colour)
        embed.title = f'{user.display_name}\'s progression'
        if count == 0:
            embed.description = 'you haven\'t picked up anything yet!'
        else:
            embed.description = f'you\'ve collected {count}/{len(f) - 2} flowers, keep it up!'
        embed.set_thumbnail(url=user.avatar_url_as())
        return await ctx.send(embed=embed)


    async def getanimeprogress(self, ctx, user):
        with open(f'cogs/leaderboards/a{ctx.guild.id}.json', 'r') as file:
            d = json.loads(file.read())

        count = 0
        for u in d['users']:
            if u['userid'] == user.id:
                count = len(u['images'])
        embed = discord.Embed(colour=ctx.guild.get_member(self.bot.user.id).colour)
        embed.title = f'{user.display_name}\'s progression'
        if count == 0:
            embed.description = 'you haven\'t picked up anything yet!'
        else:
            embed.description = f'you\'ve collected {count}/5000 characters, keep it up!'
        embed.set_thumbnail(url=user.avatar_url_as())
        return await ctx.send(embed=embed)

    async def getflowernames(self):
        with open(f'cogs/flowers.json', 'r') as file:
            f = json.loads(file.read())

        temp = []
        for cat in f:
            for flower in f[cat]:
                temp.append(list(flower.items())[0][0])

        return temp

    async def gethoots(self, uid, sid):
        with open(f'cogs/leaderboards/lb{sid}.json', 'r') as file:
            d = json.loads(file.read())
        for user in d['users']:
            if user['userid'] == uid:
                return user['images'][0]["count"]
        return False

    @commands.command(name='hoot', help='hoot')
    async def hoot(self, ctx):
        matt = 178806981128093697
        plant = 813532137050341407
        await leaderboard.Leaderboard.addpoint(self, matt, plant, "hoot hoot", 0)
        return await ctx.send(f"You've given Matt a hoot hoot, he now has {await self.gethoots(matt, plant)} hoot hoots")

    @commands.command(name='loader', hidden=True)
    @commands.is_owner()
    async def loader(self, ctx, *, module):
        try:
            await self.bot.load_extension(f'cogs.{module}')
        except Exception as e:
            await ctx.send('{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send(f'{module} loaded')

    @progression.error
    async def progressionerror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send('please format as `.progression [event name]`')

def setup(bot):
    bot.add_cog(Interactive(bot))

