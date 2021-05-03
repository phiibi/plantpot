import discord
import asyncio

from datetime import datetime
from sqlite3 import connect
from discord.ext import commands



class Reminder(commands.Cog):

    version = "1.1"

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
            CREATE TABLE IF NOT EXISTS dm_reminders (
                reminder_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                body TEXT NOT NULL,
                time TEXT NOT NULL
            )
        """)

        self.executesql("""
            CREATE TABLE IF NOT EXISTS guild_reminders (
                guild_reminder_id INTEGER PRIMARY KEY,
                server_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                body TEXT NOT NULL,
                time TEXT NOT NULL
            )
        """)

    def executesql(self, statement, data=()):
        self.cursor.execute(statement, data)
        self.conn.commit()
        return self.cursor.fetchall()

    @commands.command(name='reminder', help='manage your plant reminders')
    async def reminder(self, ctx):
        isDM = (type(ctx.channel) == discord.DMChannel)

        if not isDM:
            if not ctx.author.permissions_in(ctx.channel).manage_guild:
                return

        embed = discord.Embed(title='Reminder Menu',
                              description='Loading...')
        if not isDM:
            embed.colour = ctx.guild.get_member(self.bot.user.id).colour

        m = await ctx.send(embed=embed)

        for e in self.EMOJIS.values():
            await m.add_reaction(e)

        await self.remindermainmenu(ctx, m, isDM)

        if not isDM:
            await m.clear_reactions()
            embed.description = 'Finished'
            await m.edit(embed=embed)

    async def remindermainmenu(self, ctx, m, isDM):
        def check(r, u):
            return u.id == ctx.author.id and r.message.id == m.id

        if isDM:
            reminderlist = self.executesql('SELECT reminder_id, body FROM dm_reminders WHERE user_id = ?', (ctx.author.id,))
        else:
            reminderlist = self.executesql('SELECT guild_reminder_id, body FROM guild_reminders WHERE server_id = ?', (ctx.guild.id,))
        page = 0

        while True:
            embed = discord.Embed(title='Select a Reminder',
                                  description='React a number to select a reminder\nReact :arrow_left: to go backwards a page\nReact :arrow_right: to go forward a page\nReact :new: to create a new reminder\nReact :eject: to quit')
            if len(reminderlist):
                embed.add_field(name=f'Available reminders ({page * 10 + 1}-{min(page * 10 + 10, len(reminderlist))}/{len(reminderlist)})',
                                value="\n".join(f'{self.EMOJIS[str(i)]} {reminderlist[page*10 + i][1]}' for i in range(0, len(reminderlist[page*10:page*10+10]))))
            else:
                embed.add_field(name='Your reminders (0/0)',
                                value='None')

            if not isDM:
                embed.colour = ctx.guild.get_member(self.bot.user.id).colour

            await m.edit(embed=embed)

            try:
                r, u = await self.bot.wait_for("reaction_add", check=check, timeout=60)
            except asyncio.TimeoutError:
                if isDM:
                    embed = discord.Embed(title='Reminder Menu',
                                          description='Finished')
                    try:
                        m = await ctx.fetch_message(m.id)
                        await m.delete()
                        await ctx.send(embed=embed)
                    except discord.errors.NotFound:
                        pass
                    return
                else:
                    return

            await m.remove_reaction(r, u)

            if r.emoji == self.EMOJIS['left_arrow']:
                page -= 1
                page %= ((len(reminderlist) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS['right_arrow']:
                page += 1
                page %= ((len(reminderlist) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS['new']:
                if isDM:
                    await m.delete()
                await self.makereminder(ctx, isDM, m)
                if not isDM:
                    reminderlist = self.executesql('SELECT guild_reminder_id, body FROM guild_reminders WHERE server_id = ?', (ctx.guild.id,))
                    page = 0
            elif r.emoji == self.EMOJIS['eject']:
                if isDM:
                    await m.delete()
                if not isDM:
                    await m.remove_reaction(r, u)
                return
            elif r.emoji in self.EMOJIS.values():
                if page*10 + int(r.emoji[0]) < len(reminderlist):
                    if isDM:
                        await m.delete()
                        await self.dm_editreminder(ctx, reminderlist[page*10 + int(r.emoji[0])][0])
                    else:
                        await self.guild_editreminder(ctx, m, reminderlist[page*10 + int(r.emoji[0])][0])
                        reminderlist = self.executesql('SELECT guild_reminder_id, body FROM guild_reminders WHERE server_id = ?', (ctx.guild.id,))
                        page = 0

    async def makereminder(self, ctx, isDM, m):
        def check(r, u):
            return u == ctx.author and r.emoji == self.EMOJIS["eject"]

        if isDM:
            premiumcheck = (not len(self.executesql("""SELECT user_id
                                                       FROM premium_users 
                                                       WHERE user_id = ?""", (ctx.author.id,))) and len(self.executesql("""SELECT reminder_id 
                                                                                                                           FROM dm_reminders 
                                                                                                                           WHERE user_id = ?""", (ctx.author.id,))) >= 3)
        else:
            premiumcheck = (not len(self.executesql("""SELECT server_id
                                                       FROM premium_users 
                                                       WHERE user_id = ?""", (ctx.guild.id,))) and len(self.executesql("""SELECT guild_reminder_id 
                                                                                                                          FROM guild_reminders 
                                                                                                                          WHERE server_id = ?""", (ctx.guild.id,))) >= 3)
        if premiumcheck:
            embed = discord.Embed(title='Reminder - New Reminder',
                                  description='You need to purchase premium to have more than 3 reminders!\nReact :eject: or wait 60s to go back')
            if isDM:
                m = await ctx.send(embed=embed)
            else:
                embed.colour = ctx.guild.get_member(self.bot.user.id).colour
                await m.edit(embed=embed)
            try:
                r, u = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            except asyncio.TimeoutError:
                if isDM:
                    pass
                else:
                    return
            await m.delete()
            return await self.reminder(ctx)

        body = await self.makebody(ctx, isDM, m)

        if not body:
            if isDM:
                return self.reminder(ctx)
            return

        time = await self.maketime(ctx, isDM, m)

        if not time:
            if isDM:
                return self.reminder(ctx)
            return

        if not isDM:
            channelid = await self.makechannel(ctx, m)

            if not channelid:
                return

        if isDM:
            self.executesql('INSERT INTO dm_reminders (user_id, body, time) VALUES (?, ?, ?)', (ctx.author.id, body, time))
        else:
            self.executesql('INSERT INTO guild_reminders (server_id, channel_id, body, time) VALUES (?, ?, ?, ?)', (ctx.guild.id, channelid, body, time))

        if isDM:
            await self.reminder(ctx)

    async def makebody(self, ctx, isDM, m):
        def check(msg):
            return msg.channel == ctx.channel and msg.author == ctx.author

        embed = discord.Embed(title='Set Reminder Text',
                              description='Reply the text of the reminder, or wait 60s to go back')
        if isDM:
            m = await ctx.send(embed=embed)
        else:
            embed.colour = ctx.guild.get_member(self.bot.user.id).colour
            await m.edit(embed=embed)
        while True:
            try:
                body = await self.bot.wait_for('message', check=check, timeout=60)

                if not isDM:
                    await body.delete()

                body = body.content

                if len(body) >= 1024:
                    embed.description = 'Please use fewer than 1024 characters\nPlease try again or wait 60s to go back'
                    await m.edit(embed=embed)
                else:
                    if isDM:
                        await m.delete()
                    return body
            except asyncio.TimeoutError:
                if isDM:
                    await m.delete()
                return

    async def maketime(self, ctx, isDM, m):
        def hourcheck(r, u):
            return u == ctx.author and r.message == m and str(r.emoji) in self.HOUR_EMOJIS

        def quartercheck(r, u):
            return u == ctx.author and r.message == m and str(r.emoji) in self.QUARTER_EMOJIS

        def segcheck(r, u):
            return u == ctx.author and r.message == m and str(r.emoji) in self.SEGMENT_EMOJIS

        embed = discord.Embed(title='Set Reminder Time',
                              description='Loading...')
        if isDM:
            m = await ctx.send(embed=embed)
        else:
            embed.colour = ctx.guild.get_member(self.bot.user.id).colour
            await m.clear_reactions()
            await m.edit(embed=embed)

        for e in self.HOUR_EMOJIS:
            await m.add_reaction(e)

        embed.description = 'React the hour you would like your reminder at (UTC+0), or wait 60s to go back'
        await m.edit(embed=embed)

        while True:
            try:
                r, u = await self.bot.wait_for('reaction_add', check=hourcheck, timeout=60)
                if isDM:
                    await m.delete()
                break
            except asyncio.TimeoutError:
                if isDM:
                    await m.delete()
                return

        hour = self.HOUR_EMOJIS.index(str(r.emoji))

        embed.description = 'Loading...'
        if isDM:
            m = await ctx.send(embed=embed)
        else:
            await m.clear_reactions()
            await m.edit(embed=embed)

        for e in self.QUARTER_EMOJIS:
            await m.add_reaction(e)

        embed.description = 'Please react how far past the hour you would like your reminder at, or wait 60s to go back'
        await m.edit(embed=embed)

        while True:
            try:
                r, u = await self.bot.wait_for('reaction_add', check=quartercheck, timeout=60)
                if isDM:
                    await m.delete()
                break
            except asyncio.TimeoutError:
                if isDM:
                    await m.delete()
                return

        minutes = self.QUARTER_EMOJIS.index(str(r.emoji)) * 15

        embed.description = 'Loading...'
        if isDM:
            m = await ctx.send(embed=embed)
        else:
            await m.clear_reactions()
            await m.edit(embed=embed)

        for e in self.SEGMENT_EMOJIS:
            await m.add_reaction(e)

        embed.description = 'Please react whether you want your reminder in AM or PM\nReact with :sunny: for AM\nReact with :crescent_moon: for PM\nOr wait 60s to go back'
        await m.edit(embed=embed)

        while True:
            try:
                r, u = await self.bot.wait_for('reaction_add', check=segcheck, timeout=60)
                if isDM:
                    await m.delete()
                break
            except asyncio.TimeoutError:
                if isDM:
                    await m.delete()
                return

        hour += self.SEGMENT_EMOJIS.index(str(r.emoji)) * 12

        return f'{hour}:{minutes}'

    async def makechannel(self, ctx, m):
        def check(msg):
            return msg.channel == ctx.channel and msg.author == ctx.author

        await m.clear_reactions()
        embed = discord.Embed(title='Set Reminder Channel',
                              description='Mention the channel you would like your reminder in, or wait 60s to go back',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        await m.edit(embed=embed)

        while True:
            try:
                channel = await self.bot.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                return

            await channel.delete()

            if not len(channel.channel_mentions):
                embed.description = 'Please make sure to mention the channel, or wait 60s to go back'
                await m.edit(embed=embed)
            else:
                return channel.channel_mentions[0].id

    async def dm_editreminder(self, ctx, reminderid):
        emojis = ['\U0001F4DD', '\U0001F552', str(self.EMOJIS['asterisk']), str(self.EMOJIS['eject'])]
        reminder = self.executesql('SELECT body, time FROM dm_reminders WHERE reminder_id = ?', (reminderid,))

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
            body = await self.makebody(ctx, True, m)
            self.executesql('UPDATE dm_reminders SET body = ? WHERE reminder_id = ?', (body, reminderid))
            return
        elif str(r.emoji) == emojis[1]:
            time = await self.maketime(ctx, True, m)
            self.executesql('UPDATE dm_reminders SET time = ? WHERE reminder_id = ?', (time, reminderid))
            return await self.reminder(ctx)
        elif str(r.emoji) == emojis[2]:
            await self.delete_dm_reminder(ctx, reminderid)
            return await self.reminder(ctx)
        elif str(r.emoji) == emojis[3]:
            return await self.reminder(ctx)

    async def guild_editreminder(self, ctx, m, reminderid):
        reminder = self.executesql('SELECT channel_id, body, time FROM guild_reminders WHERE guild_reminder_id = ?', (reminderid,))

        def check(r, u):
            return u == ctx.message.author and r.message == m

        while True:
            for e in self.EMOJIS.values():
                await m.add_reaction(e)

            embed = discord.Embed(title='Edit your reminder',
                                  description='React :zero: to edit the reminder channel\nReact :one: to edit the reminder text\nReact :two: to edit the time of the reminder\nReact :asterisk: to delete the reminder\nReact :eject: to go back',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)

            embed.add_field(name='Reminder Channel', value=ctx.guild.get_channel(reminder[0][0]).mention, inline=False)
            embed.add_field(name='Text', value=reminder[0][1])
            t = reminder[0][2]
            if t.endswith(':0'):
                t = t + '0'
            embed.add_field(name='Time', value=t)

            await m.edit(embed=embed)

            try:
                r, u = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            except asyncio.TimeoutError:
                return
            
            await m.remove_reaction(r, u)

            if r.emoji == self.EMOJIS['0']:
                channelid = await self.makechannel(ctx, m)
                self.executesql('UPDATE guild_reminders SET channel_id = ? WHERE guild_reminder_id = ?', (channelid, reminderid))
                reminder = self.executesql('SELECT channel_id, body, time FROM guild_reminders WHERE guild_reminder_id = ?', (reminderid,))
            elif r.emoji == self.EMOJIS['1']:
                body = await self.makebody(ctx, False, m)
                self.executesql('UPDATE guild_reminders SET body = ? WHERE guild_reminder_id = ?', (body, reminderid))
                reminder = self.executesql('SELECT channel_id, body, time FROM guild_reminders WHERE guild_reminder_id = ?', (reminderid,))
            elif r.emoji == self.EMOJIS['2']:
                time = await self.maketime(ctx, False, m)
                await m.clear_reactions()
                self.executesql('UPDATE guild_reminders SET time = ? WHERE guild_reminder_id = ?', (time, reminderid))
                reminder = self.executesql('SELECT channel_id, body, time FROM guild_reminders WHERE guild_reminder_id = ?', (reminderid,))
            elif r.emoji == self.EMOJIS['asterisk']:
                await self.delete_guild_reminder(ctx, m, reminderid)
                return
            elif r.emoji == self.EMOJIS['eject']:
                return

    async def delete_dm_reminder(self, ctx, reminderid):
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
            self.executesql('DELETE FROM dm_reminders WHERE reminder_id = ?', (reminderid,))
            return
        else:
            return

    async def delete_guild_reminder(self, ctx, m, reminderid):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        embed = discord.Embed(title='Delete your reminder',
                              description='Are you sure you would like to delete this reminder? [(y)es/(n)o]',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        await m.edit(embed=embed)

        while True:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)
                if msg.content.lower() not in ['y', 'yes', 'n', 'no']:
                    embed.description = "Answer not recognised, would you like to delete this reminder? [(y)es/(n)o]"
                    await m.edit(embed=embed)
                else:
                    break
            except asyncio.TimeoutError:
                return

        await msg.delete()

        if msg.content.lower() in ['y', 'yes']:
            self.executesql('DELETE FROM guild_reminders WHERE guild_reminder_id = ?', (reminderid,))
            return
        else:
            return


def setup(bot):
    bot.add_cog(Reminder(bot))

