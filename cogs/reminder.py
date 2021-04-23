import discord
from discord.ext import commands
import asyncio
import datetime

from sqlite3 import connect



class Reminder(commands.Cog):

    version = "0.1"

    conn = connect("database.db")
    cursor = conn.cursor()

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
        "new":            "🆕",
        "record_button":  "⏺️",
        "asterisk":       "*️⃣",
        "eject":          "⏏️",
    }
    DEFAULT_ANSWER_EMOJIS = ["🇦", "🇧", "🇨", "🇩"]
    HOUR_EMOJIS = ['\U0001F55B', '\U0001F550', '\U0001F551', '\U0001F552',
                   '\U0001F553', '\U0001F554', '\U0001F555', '\U0001F556',
                   '\U0001F557', '\U0001F558', '\U0001F559', '\U0001F55A']
    QUARTERS_EMOJIS = ['\U0001F55B', '\U0001F552', '\U0001F555', '\U0001F558']
    SEGMENT_EMOJIS = ['\U00002600', '\U0001F319']
    def __init__(self, bot):

        self.bot = bot

        self.executesql("PRAGMA foreign_keys = ON")
        # Allows foreign keys.

        self.executesql("""
            CREATE TABLE IF NOT EXISTS reminders (
                reminder_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                body TEXT NOT NULL,
                time TEXT NOT NULL
            )
        """)

    def executesql(self, statement, data = ()):

        self.cursor.execute(statement, data)
        self.conn.commit()
        return self.cursor.fetchall()

    @commands.command(name='reminder', help='manage your plant reminders')
    @commands.dm_only()
    async def reminder(self, ctx):
        embed = discord.Embed(title='Reminder Menu',
                              description='Loading...')
        m = await ctx.send(embed=embed)

        for e in self.EMOJIS.values():
            await m.add_reaction(e)

        await self.remindermainmenu(ctx, m)

        embed = discord.Embed(title='Reminder Menu',
                              description='Finished')
        await m.edit(embed=embed)

    async def remindermainmenu(self, ctx, m):
        def check(r, u):
            return u.id == ctx.author.id and r.message.id == m.id

        reminderlist = self.executesql('SELECT reminder_id, body, time FROM reminders WHERE user_id = ?', (ctx.author.id,))
        page = 0

        embed = discord.Embed(title='Select a Reminder',
                              description='React a number to select a reminder \nReact :arrow_left: to go backwards a page \nReact :arrow_right: to go forward a page \nReact :new: to create a new reminder \nReact :eject: to quit')
        if len(reminderlist):
            embed.add_field(name=f'Available events ({page * 10 + 1} - {min(page * 10 + 10, len(reminderlist))} / {len(reminderlist)})',
                            value="\n".join(f'{self.EMOJIS[str(i)]} {reminderlist[page*10 + i][1]}' for i in range(0, len(reminderlist[page*10:page*10+10]))))
        else:
            embed.add_field(name='Your reminders (0-0/0)',
                            value='None')
        await m.edit(embed=embed)

        while True:
            try:
                r, u = await self.bot.wait_for("reaction_add", check=check, timeout=60)
            except asyncio.TimeoutError:
                return
            await m.delete()

            if r.emoji == self.EMOJIS['left_arrow']:
                page -= 1
                page %= ((len(reminderlist) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS['right_arrow']:
                page += 1
                page %= ((len(reminderlist) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS['new']:
                await self.makereminder(ctx)

    async def makereminder(self, ctx):

        body = await self.makebody(ctx)

        if not body:
            return

        time = await self.maketime(ctx)

        if not time:
            return


    async def makebody(self, ctx):
        def tcheck(m):
            return m.channel == ctx.channel and m.author == ctx.author

        embed = discord.Embed(title='Set Reminder Text',
                              description='Reply the text of the reminder, or wait 60s to go back')
        m = await ctx.send(embed=embed)
        while True:
            try:
                body = await self.bot.wait_for('message', check=tcheck, timeout=60)
                body = body.content
                await m.delete()
                return body
            except asyncio.TimeoutError:
                await m.delete()
                return

    async def maketime(self, ctx):
        def hourcheck(r, u):
            return u == ctx.author and r.message == m and str(r.emoji) in self.HOUR_EMOJIS

        def segcheck(r, u):
            return u == ctx.author and r.message == m and str(r.emoji) in self.SEGMENT_EMOJIS

        embed = discord.Embed(title='Set Reminder Time',
                              description='Loading...')
        m = await ctx.send(embed=embed)

        for e in self.HOUR_EMOJIS:
            await m.add_reaction(e)

        embed.description = 'React the hour you would like your reminder at (UTC+0), or wait 60s to go back'
        await m.edit(embed=embed)

        while True:
            try:
                r, u = await self.bot.wait_for('reaction_add', check=hourcheck, timeout=60)
                await m.delete()
                break
            except asyncio.TimeoutError:
                await m.delete()
                return

        time = self.HOUR_EMOJIS.index(str(r.emoji))

        embed.description = 'Loading...'
        m = await ctx.send(embed=embed)

        for e in self.SEGMENT_EMOJIS:
            await m.add_reaction(e)

        embed.description = 'Please react whether you want your reminder in AM or PM\nReact with :sunny: for AM\nReact with :crescent_moon: for PM\nOr wait 60s to go back'
        await m.edit(embed=embed)

        while True:
            try:
                r, u = await self.bot.wait_for('reaction_add', check=segcheck, timeout=60)
                await m.delete()
                break
            except asyncio.TimeoutError:
                await m.delete()
                return

        time += self.SEGMENT_EMOJIS.index(str(r.emoji)) * 12

        return time


def setup(bot):
    bot.add_cog(Reminder(bot))

