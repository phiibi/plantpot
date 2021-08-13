#admin.py

import discord
import os
import json

from discord.ext import commands, tasks
from aiosqlite import connect
from cogs import checkers, leaderboard
from cogs.inventory import Inventory
from cogs.badges import Badge

class Admin(commands.Cog):
    version = '0.1'
    def __init__(self, bot):
        self.bot = bot

        self.setup.start()

    @tasks.loop(count=1)
    async def setup(self):
        await self.executesql("PRAGMA foreign_keys = ON")

    @setup.before_loop
    async def before_setup(self):
        await self.bot.wait_until_ready()

    async def executesql(self, statement, data=()):
        db = await connect('database.db')
        cursor = await db.execute(statement, data)
        await db.commit()
        rows = await cursor.fetchall()
        await cursor.close()
        await db.close()
        return list(rows)

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

    @commands.command(name='tp', hiddemn=True)
    @checkers.is_plant_owner()
    async def tp(self, ctx, user:discord.Member, quantity:int, *, name):
        if name.lower() in ['batch']:
            items = await self.executesql("SELECT image_id, event_id FROM images WHERE text LIKE '%stripe' AND event_id = ?", (1,))
            for stripe in items:
                await Inventory.additem(self, user.id, ctx.guild.id, stripe[1], stripe[0], quantity)
            await ctx.send('*teleports behind you* nothing personal kid')
            return
        item = await self.executesql('SELECT image_id, event_id FROM images WHERE lower(text) = ?', (name.lower(),))
        if len(item):
            await Inventory.additem(self, user.id, ctx.guild.id, item[0][1], item[0][0], quantity)
            await ctx.send('*teleports behind you* nothing personal kid')
        else:
            await ctx.send('Item not found')

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

    @commands.command(name='givebadges', hidden=True)
    @checkers.is_plant_owner()
    async def givebadges(self, ctx, event, *, name):
        top10 = await self.executesql('SELECT lb.user_id FROM leaderboards lb INNER JOIN events e USING (event_id) WHERE e.name = ? AND lb.server_id = ? ORDER BY lb.score LIMIT 10', (event, ctx.guild.id))

        for userid in top10:
            user = await self.bot.fetch_user(userid)
            if user is None:
                await ctx.send(f'Could not find user id {userid}')
            else:
                await Badge.give(self, ctx, user, name)

        return await ctx.send('Badges distributed')

def setup(bot):
    bot.add_cog(Admin(bot))
