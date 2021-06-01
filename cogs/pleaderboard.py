#leaderboard.py


import asyncio
import discord

from discord.ext import commands, tasks
from aiosqlite import connect

class PrideLeaderboard(commands.Cog):
    version = '1.0'

    EMOJIS = {
        "0":              "0️⃣",
        "1":              "1️⃣",
        "2":              "2️⃣",
        "3":              "3️⃣",
        "4":              "4️⃣",
        "5":              "5️⃣",
        "6":              "6️⃣",
        "7":              "7️⃣",
        "8":              "8️⃣",
        "9":              "9️⃣",
        "left_arrow":     "⬅️",
        "right_arrow":    "➡️",
        "eject":          "⏏️",
    }

    def __init__(self, bot):

        self.bot = bot

        self.setup.start()

    @tasks.loop(count=1)
    async def setup(self):
        await self.executesql("PRAGMA foreign_keys = ON")

        await self.executesql("""CREATE TABLE IF NOT EXISTS leaderboards (
                    lb_id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    event_id INTEGER NOT NULL,
                    server_id INTEGER NOT NULL,
                    score INTEGER NOT NULL,
                    CONSTRAINT fk_event FOREIGN KEY (event_id) REFERENCES events(event_id))""")

    @setup.before_loop
    async def before_setup(self):
        await self.bot.wait_until_ready()

    #executesql is now asynchronous to prevent blocking
    async def executesql(self, statement, data=()):
        db = await connect('database.db')
        cursor = await db.execute(statement, data)
        await db.commit()
        rows = await cursor.fetchall()
        await cursor.close()
        await db.close()

        #returns a list of Row objects which can be indexed like an array
        return list(rows)

    @commands.command(name='prideleaderboard', help='displays leaderboard', aliases=['top10', 'top', 'lb'])
    async def leaderboardmenu(self, ctx, *, eventname=None):
        def check(r, u):
            return u == ctx.author and r.message == m

        embed = discord.Embed(title='Leaderboard Menu',
                              description='Loading...',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        m = await ctx.send(embed=embed)

        eventname = 'pride'

        if eventname is not None:
            checklb = await self.executesql('SELECT DISTINCT lb.event_id, e.name FROM leaderboards lb INNER JOIN events e USING (event_id) WHERE lb.server_id = ? AND lower(e.name) = ?', (ctx.guild.id, eventname.lower()))
            if len(checklb):
                return await self.displayleaderboard(ctx, m, checklb[0][0], checklb[0][1])

        leaderboards = await self.executesql('SELECT DISTINCT lb.event_id, e.name FROM leaderboards lb INNER JOIN events e USING (event_id) WHERE lb.server_id = ?', (ctx.guild.id,))
        page = 0

        for e in self.EMOJIS.values():
            await m.add_reaction(e)

        while True:
            embed = discord.Embed(title='Leaderboard Menu',
                                  description='React a number to select a leaderboard',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)

            if len(leaderboards):
                embed.add_field(name=f'Available leaderboards ({page * 10 + 1}-{min(page * 10 + 10, len(leaderboards))}/{len(leaderboards)})',
                                value="\n".join(f'{self.EMOJIS[str(i)]} {leaderboards[page*10 + i][1]}' for i in range(0, len(leaderboards[page*10:page*10+10]))))
            else:
                embed.add_field(name='Available leaderboards (0-0/0)',
                                value='None')
            await m.edit(embed=embed)

            try:
                r, u = await self.bot.wait_for("reaction_add", check=check, timeout=60)
            except asyncio.TimeoutError:
                return
            await m.remove_reaction(r, u)

            if r.emoji == self.EMOJIS["left_arrow"]:
                page -= 1
                page %= ((len(leaderboards) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS["right_arrow"]:
                page += 1
                page %= ((len(leaderboards) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS["eject"]:
                return await m.delete()
            elif r.emoji in self.EMOJIS.values():
                if page*10 + int(r.emoji[0]) < len(leaderboards):
                    return await self.displayleaderboard(ctx, m, leaderboards[page*10 + int(r.emoji[0])][0], leaderboards[page*10 + int(r.emoji[0])][1])

    @commands.command(name='myleaderboard', help='displays leaderboard position', aliases=['mylb', 'mytop10', 'mypos'])
    async def myleaderboardmenu(self, ctx, *, eventname=None):
        def check(r, u):
            return u == ctx.author and r.message == m

        embed = discord.Embed(title='Leaderboard Menu',
                              description='Loading...',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        m = await ctx.send(embed=embed)

        eventname = 'pride'

        if eventname is not None:
            checklb = await self.executesql('SELECT DISTINCT lb.event_id, lb.score FROM leaderboards lb INNER JOIN events e USING (event_id) WHERE lb.server_id = ? AND lb.user_id = ? AND lower(e.name) = ?', (ctx.guild.id, ctx.author.id, eventname.lower()))
            if len(checklb):
                return await self.displayposition(ctx, m, checklb[0][0], checklb[0][1])

        leaderboards = await self.executesql('SELECT DISTINCT lb.event_id, lb.score, e.name FROM leaderboards lb INNER JOIN events e USING (event_id) WHERE lb.server_id = ? AND lb.user_id = ?', (ctx.guild.id, ctx.author.id))
        page = 0

        for e in self.EMOJIS.values():
            await m.add_reaction(e)

        while True:
            embed = discord.Embed(title='Leaderboard Menu',
                                  description='React a number to select a leaderboard',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)

            if len(leaderboards):
                embed.add_field(name=f'Available leaderboards ({page * 10 + 1}-{min(page * 10 + 10, len(leaderboards))}/{len(leaderboards)})',
                                value="\n".join(f'{self.EMOJIS[str(i)]} {leaderboards[page*10 + i][2]}' for i in range(0, len(leaderboards[page*10:page*10+10]))))
            else:
                embed.add_field(name='Available leaderboards (0-0/0)',
                                value='None')
            await m.edit(embed=embed)

            try:
                r, u = await self.bot.wait_for("reaction_add", check=check, timeout=60)
            except asyncio.TimeoutError:
                return
            await m.remove_reaction(r, u)

            if r.emoji == self.EMOJIS["left_arrow"]:
                page -= 1
                page %= ((len(leaderboards) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS["right_arrow"]:
                page += 1
                page %= ((len(leaderboards) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS["eject"]:
                return await m.delete()
            elif r.emoji in self.EMOJIS.values():
                if page*10 + int(r.emoji[0]) < len(leaderboards):
                    return await self.displayposition(ctx, m, leaderboards[page*10 + int(r.emoji[0])][0], leaderboards[page*10 + int(r.emoji[0])][1])

    async def displayleaderboard(self, ctx, m, eventid, eventname):
        await m.clear_reactions()

        users = await self.executesql('SELECT user_id, score FROM leaderboards WHERE event_id = ? AND server_id = ? ORDER BY score DESC LIMIT 10', (eventid, ctx.guild.id))

        embed = discord.Embed(title=f'{eventname} top {len(users)}',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        lbtxt = ''
        for i in range(0, len(users)):
            user = await self.bot.fetch_user(users[i][0])
            lbtxt += f'{i+1}. **{user.display_name}** - {users[i][1]}\n'
        embed.description = lbtxt
        await m.edit(embed=embed)

    async def displayposition(self, ctx, m, eventid, score):
        await m.clear_reactions()

        users = await self.executesql('SELECT COUNT(*) FROM leaderboards WHERE score > ?', (score,))
        items = await self.executesql('SELECT SUM(count) FROM inventories WHERE event_id = ? AND server_id = ? AND user_id = ?', (eventid, ctx.guild.id, ctx.author.id))

        embed = discord.Embed(title=f'You are in #{users[0][0] + 1} place!',
                              description=f'You have collected {items[0][0]} items so far, totalling {score} points! Keep it up!',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        embed.set_thumbnail(url=ctx.author.avatar_url_as())
        await m.edit(embed=embed)

    async def addpoints(self, userid, serverid, eventid, points):
        userpoints = await self.executesql('SELECT lb_id, score FROM leaderboards WHERE user_id = ? AND server_id = ? AND event_id = ?', (userid, serverid, eventid))

        if len(userpoints):
            await self.executesql('UPDATE leaderboards SET score = ? WHERE lb_id = ?', (userpoints[0][1] + points, userpoints[0][0]))
        else:
            await self.executesql('INSERT INTO leaderboards (user_id, event_id, server_id, score) VALUES (?, ?, ?, ?)', (userid, eventid, serverid, points))

def setup(bot):
    bot.add_cog(PrideLeaderboard(bot))
