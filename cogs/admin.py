#admin.py

import discord
import os
import json

from discord.ext import commands
from cogs import checkers, leaderboard


class Admin(commands.Cog):
    version = '0.1'
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='load', hidden=True)
    @checkers.is_plant_owner()
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
    @checkers.is_plant_owner()
    async def _reload(self, ctx, *, module: str):
        try:
            self.bot.unload_extension(f'cogs.{module}')
            self.bot.load_extension(f'cogs.{module}')
        except Exception as e:
            await ctx.send('{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send(f'{module} reloaded')

    @commands.command(name="refresh", hidden=True)
    @checkers.is_plant_owner()
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

    @commands.command(name='kill', help='wrong lever!', hidden=True)
    @commands.is_owner()
    async def kill(self, ctx):
        await ctx.send('shutting down plant')
        await ctx.bot.logout()

    @commands.command(name='teleports', hidden=True)
    @checkers.is_plant_owner()
    async def teleports(self, ctx, user: discord.Member, points: int, url,  *, name):
        await leaderboard.AnimeLeaderboard.addpoint(self, user.id, ctx.guild.id, url, name, points)
        await ctx.send('*teleports behind you* nothing personal kid')

    @commands.command(name='remove', hidden=True)
    @checkers.is_plant_owner()
    async def remove(self, ctx, user: discord.Member, points: int, *, name):
        with open(f'cogs/leaderboards/a{ctx.guild.id}.json', 'r') as file:
            d = json.loads(file.read())
        removed = False
        for u in d['users']:
            if u['userid'] == user.id:
                for image in u['images']:
                    if image['name'].lower() == name.lower():
                        u['images'].remove(image)
                        u['points'] -= points
                        removed = True
        if removed:
            with open(f'cogs/leaderboards/a{ctx.guild.id}.json', 'w') as file:
                json.dump(d, file)
            await ctx.send(f'Removed {name} from {user.mention}\'s inventory')
        else:
            await ctx.send(f"Couldn't find {name} in {user.mention}'s inventory")

    @commands.command(name='stop', hidden=True)
    @checkers.is_plant_owner()
    async def delete(self, ctx, msgid):
        msg = await ctx.channel.fetch_message(msgid)
        await msg.delete()

    @commands.command(name='gift', hidden=True)
    @checkers.is_plant_owner()
    async def gifting(self, ctx, user: discord.Member, *, name):
        await leaderboard.Leaderboard.addpoint(self, user.id, ctx.guild.id, name, 0)

    @commands.command(name='blacklist', hidden=True)
    @checkers.is_plant_owner()
    async def blacklist(self, ctx, user: discord.Member):
        with open(f'cogs/userblacklist.json', 'r') as file:
            d = json.loads(file.read())
        if d['id'].count(user.id):
            return await ctx.send('this user is already blacklisted')
        else:
            d['id'].append(user.id)
            await ctx.send(f'{user.mention} has been blacklisted')
        with open(f'cogs/userblacklist.json', 'w') as file:
            json.dump(d, file)

    @commands.command(name='whitelist', hidden=True)
    @checkers.is_plant_owner()
    async def whitelist(self, ctx, user: discord.Member):
        with open(f'cogs/userblacklist.json', 'r') as file:
            d = json.loads(file.read())
        if d['id'].count(user.id):
            d['id'].remove(user.id)
            await ctx.send(f'{user.mention} has been removed from the blacklist')
        else:
            return await ctx.send('user was not on the blacklist')
        with open(f'cogs/userblacklist.json', 'w') as file:
            json.dump(d, file)

    @commands.command(name='fixerupper', hidden=True)
    @commands.is_owner()
    async def fixinv(self, ctx):
        with open('cogs/leaderboards/a817563329747877909.json', 'r') as f:
            d = json.loads(f.read())
        for user in d['users']:
            temp = []
            for i in range(len(user['image_name'])):
                temp.append({"name": user['image_name'][i],
                             "url": user['image_url'][i]})
            user.pop("image_name")
            user.pop("image_url")
            user.update({"images": temp})
        with open('cogs/leaderboards/a817563329747877909.json', 'w') as f:
            json.dump(d, f)
        await ctx.send('anime done')


def setup(bot):
    bot.add_cog(Admin(bot))
