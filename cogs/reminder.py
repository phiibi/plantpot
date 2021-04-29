import discord
import asyncio

from datetime import datetime
from sqlite3 import connect
from discord.ext import commands, tasks



class Reminder(commands.Cog):

    version = "1.0"

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
        "asterisk":       "*️⃣",
        "eject":          "⏏️",
    }
    HOUR_EMOJIS = ['\U0001F55B', '\U0001F550', '\U0001F551', '\U0001F552',
                   '\U0001F553', '\U0001F554', '\U0001F555', '\U0001F556',
                   '\U0001F557', '\U0001F558', '\U0001F559', '\U0001F55A']
    QUARTER_EMOJIS = ['\U0001F55B', '\U0001F552', '\U0001F555', '\U0001F558']
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

    def executesql(self, statement, data=()):
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

    async def remindermainmenu(self, ctx, m):
        def check(r, u):
            return u.id == ctx.author.id and r.message.id == m.id

        reminderlist = self.executesql('SELECT reminder_id, body FROM reminders WHERE user_id = ?', (ctx.author.id,))
        page = 0

        embed = discord.Embed(title='Select a Reminder',
                              description='React a number to select a reminder \nReact :arrow_left: to go backwards a page \nReact :arrow_right: to go forward a page \nReact :new: to create a new reminder \nReact :eject: to quit')
        if len(reminderlist):
            embed.add_field(name=f'Available reminders ({page * 10 + 1}-{min(page * 10 + 10, len(reminderlist))}/{len(reminderlist)})',
                            value="\n".join(f'{self.EMOJIS[str(i)]} {reminderlist[page*10 + i][1]}' for i in range(0, len(reminderlist[page*10:page*10+10]))))
        else:
            embed.add_field(name='Your reminders (0/0)',
                            value='None')
        await m.edit(embed=embed)

        while True:
            try:
                r, u = await self.bot.wait_for("reaction_add", check=check, timeout=60)
            except asyncio.TimeoutError:
                embed = discord.Embed(title='Reminder Menu',
                                      description='Finished')
                try:
                    m = await ctx.fetch_message(m.id)
                    await m.delete()
                    await ctx.send(embed=embed)
                except discord.errors.NotFound:
                    pass
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
            elif r.emoji == self.EMOJIS['eject']:
                return
            elif (r.emoji in self.EMOJIS.values()):
                if (page*10 + int(r.emoji[0]) < len(reminderlist)):
                    await self.editreminder(ctx, reminderlist[page*10 + int(r.emoji[0])][0])

    async def makereminder(self, ctx):
        def check(r, u):
            return u == ctx.author and r.emoji == self.EMOJIS["eject"]

        if (not len(self.executesql("""SELECT user_id
                                       FROM premium_users 
                                       WHERE user_id = ?""", (ctx.author.id,))) and len(self.executesql("""SELECT reminder_id 
                                                                                                           FROM reminders 
                                                                                                           WHERE user_id = ?""", (ctx.author.id,))) >= 3):
            embed = discord.Embed(title='Reminder - New Reminder',
                                  description='You need to purchase premium to have more than 3 reminders!\nReact :eject: or wait 60s to go back')
            m = await ctx.send(embed=embed)
            try:
                r, u = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            except asyncio.TimeoutError:
                pass
            await m.delete()
            return await self.reminder(ctx)

        body = await self.makebody(ctx)

        if not body:
            return self.reminder(ctx)

        time = await self.maketime(ctx)

        if not time:
            return self.reminder(ctx)

        self.executesql('INSERT INTO reminders (user_id, body, time) VALUES (?, ?, ?)', (ctx.author.id, body, time))

        await self.reminder(ctx)

    async def makebody(self, ctx):
        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author

        embed = discord.Embed(title='Set Reminder Text',
                              description='Reply the text of the reminder, or wait 60s to go back')
        m = await ctx.send(embed=embed)
        while True:
            try:
                body = await self.bot.wait_for('message', check=check, timeout=60)
                body = body.content
                if len(body) >= 1024:
                    embed.description = 'Please use fewer than 1024 characters\nPlease try again or wait 60s to go back'
                    await m.edit(embed=embed)
                else:
                    await m.delete()
                    return body
            except asyncio.TimeoutError:
                await m.delete()
                return

    async def maketime(self, ctx):
        def hourcheck(r, u):
            return u == ctx.author and r.message == m and str(r.emoji) in self.HOUR_EMOJIS

        def quartercheck(r, u):
            return u == ctx.author and r.message == m and str(r.emoji) in self.QUARTER_EMOJIS

        def segcheck(r, u):
            return u == ctx.author and r.message == m and str(r.emoji) in self.SEGMENT_EMOJIS

        embed = discord.Embed(title='Set Reminder Time',
                              description='Loading...')
        m = await ctx.send(embed=embed)

        for e in self.HOUR_EMOJIS:
            await m.add_reaction(e)

        embed.description = 'React the hour you would like your reminder at (UTC+1), or wait 60s to go back'
        await m.edit(embed=embed)

        while True:
            try:
                r, u = await self.bot.wait_for('reaction_add', check=hourcheck, timeout=60)
                await m.delete()
                break
            except asyncio.TimeoutError:
                await m.delete()
                return

        hour = self.HOUR_EMOJIS.index(str(r.emoji))

        embed.description = 'Loading...'
        m = await ctx.send(embed=embed)

        for e in self.QUARTER_EMOJIS:
            await m.add_reaction(e)

        embed.description = 'Please react how far past the hour you would like your reminder at, or wait 60s to go back'
        await m.edit(embed=embed)

        while True:
            try:
                r, u = await self.bot.wait_for('reaction_add', check=quartercheck, timeout=60)
                await m.delete()
                break
            except asyncio.TimeoutError:
                return

        minutes = self.QUARTER_EMOJIS.index(str(r.emoji)) * 15

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

        hour += self.SEGMENT_EMOJIS.index(str(r.emoji)) * 12

        return f'{hour}:{minutes}'

    async def editreminder(self, ctx, reminderid):
        emojis = ['\U0001F4DD', '\U0001F552', str(self.EMOJIS['asterisk']), str(self.EMOJIS['eject'])]
        reminder = self.executesql('SELECT body, time FROM reminders WHERE reminder_id = ?', (reminderid,))

        def check(r, u):
            return u == ctx.message.author and r.message == m and str(r.emoji) in emojis

        embed = discord.Embed(title='Edit your reminder',
                              description='Loading...')
        m = await ctx.send(embed=embed)

        for e in emojis:
            await m.add_reaction(e)

        embed = discord.Embed(title='Edit your reminder',
                              description='React :pencil: to edit the reminder text\nReact :clock3: to edit the time of the reminder\nReact :asterisk: to delete the reminder\nReact :eject: to go back')
        embed.add_field(name='Reminder Text', value=reminder[0][0])
        t = reminder[0][1]
        if t.endswith(':0'):
            t = t + '0'
        embed.add_field(name='Time', value=t)

        await m.edit(embed=embed)

        while True:
            try:
                r, u = await self.bot.wait_for('reaction_add', check=check, timeout=60)
                await m.delete()
                break
            except asyncio.TimeoutError:
                return

        if str(r.emoji) == emojis[0]:
            body = await self.makebody(ctx)
            self.executesql('UPDATE reminders SET body = ? WHERE reminder_id = ?', (body, reminderid))
            return
        elif str(r.emoji) == emojis[1]:
            time = await self.maketime(ctx)
            self.executesql('UPDATE reminders SET time = ? WHERE reminder_id = ?', (time, reminderid))
            return await self.reminder(ctx)
        elif str(r.emoji) == emojis[2]:
            await self.deletereminder(ctx, reminderid)
            return await self.reminder(ctx)
        elif str(r.emoji) == emojis[3]:
            return await self.reminder(ctx)

    async def deletereminder(self, ctx, reminderid):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        embed = discord.Embed(title='Delete your reminder',
                              description='Are you sure you would like to delete this reminder? [(y)es/(n)o]')
        msg = await ctx.send(embed=embed)

        while True:
            try:
                m = await self.bot.wait_for('message', check=check, timeout=60)
                if m.content.lower() not in ['y', 'yes', 'n', 'no']:
                    embed.description = "Answer not recognised, would you like to delete this reminder? [(y)es/(n)o]"
                    await msg.edit(embed=embed)
                else:
                    break
            except asyncio.TimeoutError:
                return

        await msg.delete()

        if m.content.lower() in ['y', 'yes']:
            self.executesql('DELETE FROM reminders WHERE reminder_id = ?', (reminderid,))
            return
        else:
            return


def setup(bot):
    bot.add_cog(Reminder(bot))

