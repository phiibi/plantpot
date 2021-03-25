#admin.py

import discord
import os
import json
import random

from discord.ext import commands
from cogs import profile, leaderboard, checkers
from math import floor

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='load', hidden=True)
    @commands.is_owner()
    async def load(self, ctx, *, module: str):
        """Loads a module."""
        try:
            self.bot.load_extension(f'cogs.{module}')
        except Exception as e:
            await ctx.send('{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send(f'{module} reloaded')

    @commands.command(name='unload', hidden=True)
    @commands.is_owner()
    async def unload(self, *, module: str):
        """Unloads a module."""
        try:
            self.bot.unload_extension(f'cogs.{module}')
        except Exception as e:
            await self.bot.say('\N{PISTOL}')
            await self.bot.say('{}: {}'.format(type(e).__name__, e))
        else:
            await self.bot.say('\N{OK HAND SIGN}')

    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def _reload(self, ctx, *, module: str):
        try:
            self.bot.unload_extension(f'cogs.{module}')
            self.bot.load_extension(f'cogs.{module}')
        except Exception as e:
            await ctx.send('{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send(f'{module} reloaded')


    @commands.command(name='parsa', hidden=True, help="debug")
    @commands.is_owner()
    async def parsa(self, ctx):
        sid = ctx.guild.id
        with open(f'cogs/leaderboards/a{sid}.json', 'r') as file:
            d = json.loads(file.read())
        for n, u in enumerate(d['users']):
            temp = []
            for i in u['image_name']:
                if i[0] == " ":
                    temp.append(i[1:])
                else:
                    temp.append(i)
            d['users'][n].update({"image_name": temp})
        with open(f'cogs/leaderboards/a{sid}.json', 'w') as file:
            json.dump(d, file)

    @commands.command(name="refresh", hidden=True)
    @commands.is_owner()
    async def refresh(self, ctx):
        tempstr =''
        for f in os.listdir('./cogs/'):
            if f.endswith('.py') and not f.startswith('__'):
                try:
                    self.bot.unload_extension(f'cogs.{f[:-3]}')
                    self.bot.load_extension(f'cogs.{f[:-3]}')
                except Exception as e:
                    tempstr += '{}: {}\n'.format(type(e).__name__, e)
                else:
                    tempstr += f'{f} reloaded\n'
        embed = discord.Embed()
        embed.title = 'refresh results'
        embed.description = tempstr
        await ctx.send(embed=embed)

    @commands.command(name='badgeparsa', hidden=True)
    @commands.is_owner()
    async def badgeparse(self, ctx):
        with open(f'cogs/profiles.json', 'r') as file:
            d = json.loads(file.read())
        temp = {"badges": []}
        for i in range(len(d['users'])):
            d['users'][i].update(temp)
        with open(f'cogs/profiles.json', 'w') as file:
            json.dump(d, file)

    @commands.command(name='replace', hidden=True)
    @checkers.is_plant_owner()
    async def replace(self, ctx):
        with open(f'cogs/leaderboards/lb{ctx.guild.id}.json', 'r') as file:
            d = json.loads(file.read())

        for user in d['users']:
            temp = []
            for image in user['images']:
                if image != "Rafflesia":
                    temp.append(image)
            user.update({"images": temp})
        with open(f'cogs/leaderboards/lb{ctx.guild.id}.json', 'w') as file:
            json.dump(d, file)




def setup(bot):
    bot.add_cog(Admin(bot))
