#interactive.py

import discord
import random

from discord.ext import commands

#cog for fun things
class Interactive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam = True

    @commands.command(name='avatar', help='returns my avatar')
    async def avatar(self, ctx):
        embed = discord.Embed()
        embed.title = 'here\'s my avatar!'
        embed.set_image(url='https://i.imgur.com/I9SPukW.jpg')
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


    @commands.command(name='kill', help='wrong lever!', hidden=True)
    @commands.is_owner()
    async def kill(self, ctx):
        await ctx.send('shutting down plant')
        await ctx.bot.logout()
    @commands.command(name='loader', hidden=True)
    @commands.is_owner()
    async def loader(self, ctx, *, module):
        try:
            await self.bot.load_extension(f'cogs.{module}')
        except Exception as e:
            await ctx.send('{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send(f'{module} loaded')
def setup(bot):
    bot.add_cog(Interactive(bot))

