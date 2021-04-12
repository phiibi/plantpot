# -------  Matthew Hammond, 2021  ------
# ------  Misc Plant Bot Commands  -----
# ---------------  v1.2  ---------------


import discord
from discord.ext import commands, tasks

from sqlite3 import connect
from json import loads
from operator import itemgetter

class Misc(commands.Cog):

    conn = connect("database.db")
    cursor = conn.cursor()

    def __init__(self, bot):

        self.bot = bot

        self.updateLeaderboardRoles.start()

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
        
        with open(f'cogs/leaderboards/alb813532137050341407.json', 'r') as file:
            data = loads(file.read())

        lb = data['users']
        lb.sort(key = itemgetter('points'), reverse=True)
        ids += [user["userid"] for user in lb[:min(len(lb), 10)]]
        # Gets all the ids of users in the top 10 of the anime leaderboard, and adds them to the list of regular leaderboard ids.

        server = self.bot.get_guild(813532137050341407)
        for member in server.members:
            roleIds = [role.id for role in member.roles]

            if 825240728778047568 in roleIds and member.id not in ids:
                await member.remove_roles(server.get_role(825240728778047568))
                # If the member has the role, but is not in the top 10 of a leaderboard, remove it.

            elif 825240728778047568 not in roleIds and member.id in ids:
                await member.add_roles(server.get_role(825240728778047568))
                # If the member is in the top 10 of a leaderboard, but does not have the role, add it.
    
    async def executeSQLCheck(ctx):
        return 817801520074063974 in [role.id for role in ctx.author.roles]
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