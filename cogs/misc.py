# -------  Matthew Hammond, 2021  ------
# ------  Misc Plant Bot Commands  -----
# ---------------  v1.4  ---------------


import discord
import time
import asyncio
from discord.ext import commands, tasks

from sqlite3 import connect
from datetime import datetime

from json import loads
from operator import itemgetter

class Misc(commands.Cog):

    version = "1.5"

    conn = connect("database.db")
    cursor = conn.cursor()

    def __init__(self, bot):

        self.bot = bot

        self.updateLeaderboardRoles.start()

        self.sendreminders.start()

        self.lockdiscussion.start()

        self.executeSQL("PRAGMA foreign_keys = ON")
        
    def executeSQL(self, statement, data = ()):

        self.cursor.execute(statement, data)
        self.conn.commit()
        return self.cursor.fetchall()

    @tasks.loop(seconds = 60)
    async def updateLeaderboardRoles(self):

        with open(f'cogs/leaderboards/lb813532137050341407.json', 'r') as file:
            data = loads(file.read())

        lb = data['users']
        lb.sort(key = itemgetter('points'), reverse=True)
        ids = [user["userid"] for user in lb[:min(len(lb), 10)]]
        # Gets all the ids of users in the top 10 of the regular leaderboard.

        with open(f'cogs/leaderboards/a813532137050341407.json', 'r') as file:
            data = loads(file.read())

        lb = data['users']
        lb.sort(key = itemgetter('points'), reverse=True)
        ids += [user["userid"] for user in lb[:min(len(lb), 10)]]
        # Gets all the ids of users in the top 10 of the anime leaderboard, and adds them to the list of regular leaderboard ids.

        server = await self.bot.fetch_guild(813532137050341407)
        for member in await server.fetch_members().flatten():
            roleIds = [role.id for role in member.roles]

            if (825240728778047568 in roleIds and member.id not in ids):
                await member.remove_roles(server.get_role(825240728778047568))
                # If the member has the role, but is not in the top 10 of a leaderboard, remove it.

            elif (825240728778047568 not in roleIds and member.id in ids):
                await member.add_roles(server.get_role(825240728778047568))
                # If the member is in the top 10 of a leaderboard, but does not have the role, add it.
    
    async def executeSQLCheck(ctx):
        return 817801520074063974 in [role.id for role in ctx.author.roles] or ctx.author.id == 115560604047114248
        # Must have the Dev Team role to use executeSQL.

    @commands.command(
        name = "executeSQL",
        aliases = ["esql"],
        hidden = True,
    )
    @commands.check(executeSQLCheck)
    async def eSQL(self, ctx, *execute):

        for statement in " ".join(execute).split(";"):
            try:
                data = self.executeSQL(statement)
                await ctx.send(data)
            except Exception as data:
                await ctx.send(data)

    @commands.command(
        name = "cogVersions",
        aliases = ["cv"],

        hidden = True,
    )
    async def cogVersions(self, ctx):

        embed = discord.Embed(
            title = "Cog Versions",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        for name, cog in self.bot.cogs.items():
            try:
                embed.add_field(name = name, value = "v" + cog.version)
            except AttributeError:
                embed.add_field(name = name, value = "Unspecified")
        await ctx.send(embed = embed)

    @tasks.loop(minutes=1)
    async def sendreminders(self):
        t = datetime.now()
        t = f'{t.hour - 6}:{t.minute}'

        reminderlist = self.executeSQL('SELECT user_id, body FROM dm_reminders WHERE time = ?', (t,))

        for reminder in reminderlist:
            user = self.bot.get_user(reminder[0])
            await user.send(reminder[1])

        reminderlist = self.executeSQL('SELECT channel_id, body FROM guild_reminders WHERE time = ?', (t,))

        for reminder in reminderlist:
            channel = self.bot.get_channel(reminder[0])
            await channel.send(reminder[1])

    @tasks.loop(seconds=60)
    async def lockdiscussion(self):
        t = time.gmtime(time.time())
        if self.bot.is_ready():
            if not (t[3] == 8 or t[3] == 22):
                pass

            channel = self.bot.get_channel(834839193724649492)
            role = channel.guild.get_role(750099685191974992)

            perms = channel.overwrites_for(role)
            m = perms.send_messages
            perms.read_messages = True

            if t[3] == 8 and not m:
                perms.send_messages = True
                await channel.set_permissions(role, overwrite=perms)
                await channel.edit(name='discussion topic open')
            elif t[3] == 22 and m:
                perms.send_messages = False
                await channel.set_permissions(role, overwrite=perms)
                await channel.edit(name='discussion topic closed')

    def cog_unload(self):
        self.updateLeaderboardRoles.stop()

        self.sendreminders.stop()

        self.lockdiscussion.stop()


def setup(bot):
    bot.add_cog(Misc(bot))