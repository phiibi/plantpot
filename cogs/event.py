#event.py

import os
import asyncio
import discord
import aiohttp

from base64 import b64encode

from random import random, choice
from discord.ext import commands, tasks
from dotenv import load_dotenv
from aiosqlite import connect
from time import time

load_dotenv()
IMGUR_TOKEN = os.getenv('IMGUR_TOKEN')
IMGUR_ID = os.getenv('IMGUR_ID')


class Event(commands.Cog):
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
        "new":            "🆕",
        "record_button":  "⏺️",
        "asterisk":       "*️⃣",
        "eject":          "⏏️",
    }

    def __init__(self, bot):
        self.bot = bot

        self.setup.start()

        self.defaultevent = 1

    @tasks.loop(count=1)
    async def setup(self):
        await self.executesql("PRAGMA foreign_keys = ON")

        await self.executesql("""CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY,
                server_id INTEGER NOT NULL,
                emoji TEXT NOT NULL,
                cooldown INTEGER NOT NULL,
                system_id INTEGER NOT NULL,
                name TEXT NOT NULL)""")

        await self.executesql("""CREATE TABLE IF NOT EXISTS images (
                image_id INTEGER PRIMARY KEY,
                event_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                url TEXT NOT NULL,
                imgur_id TEXT NOT NULL,
                rarity_id INTEGER NOT NULL,
                CONSTRAINT fk_rarity FOREIGN KEY (rarity_id) REFERENCES rarities(rarity_id),
                CONSTRAINT fk_event FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE)""")

        await self.executesql("""CREATE TABLE IF NOT EXISTS rarities (
                rarity_id INTEGER PRIMARY KEY,
                system_id INTEGER NOT NULL,
                rarity_name TEXT NOT NULL,
                chance REAL NOT NULL,
                points_first INTEGER NOT NULL,
                points_second INTEGER NOT NULL,
                CONSTRAINT fk_raritysys FOREIGN KEY (system_id) REFERENCES rarity_systems(system_id) ON DELETE CASCADE)""")

        await self.executesql("""CREATE TABLE IF NOT EXISTS rarity_systems (
                system_id INTEGER PRIMARY KEY,
                system_name TEXT NOT NULL)""")

        await self.executesql("""CREATE TABLE IF NOT EXISTS active_events (
                active_id INTEGER PRIMARY KEY,
                event_id INTEGER NOT NULL,
                server_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                CONSTRAINT fk_event FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE)""")

        await self.executesql("""CREATE TABLE IF NOT EXISTS active_posts (
                active_id PRIMARY KEY,
                event_id INTEGER NOT NULL,
                image_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                CONSTRAINT fk_active FOREIGN KEY (active_id) REFERENCES active_events(active_id)
                CONSTRAINT fk_event FOREIGN KEY (event_id) REFERENCES events(event_id),
                CONSTRAINT fk_image FOREIGN KEY (image_id) REFERENCES images(image_id) ON DELETE CASCADE)""")

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

    async def eventWizardCheck(ctx):
        return 825241813505802270 in [role.id for role in ctx.author.roles]
        #return ctx.author.permissions_in(ctx.channel).manage_guild or 825241813505802270 in [role.id for role in ctx.author.roles]

    async def rarityWizardCheck(ctx):
        return ctx.author.id in [115560604047114248, 579785620612972581]


#
#
# ------------------- MENUS ------------------- #
#
#

    @commands.command(name='eventwizard', aliases=['ewiz', 'ew'], usage='eventwizard', help='create or edit your own events', hidden=True)
    @commands.check(eventWizardCheck)
    async def eventwizard(self, ctx):
        embed = discord.Embed(title='Event Wizard',
                              description='Loading...',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        m = await ctx.send(embed=embed)

        for e in self.EMOJIS.values():
            await m.add_reaction(e)

        await self.eventmenu(ctx, m)

        embed.description = 'Finished'

        await m.edit(embed=embed)
        await m.clear_reactions()

    #Displays all available events
    async def eventmenu(self, ctx, m):
        def check(r, u):
            return u == ctx.author and r.message == m

        eventlist = await self.executesql('SELECT event_id, name FROM events WHERE server_id = ?', (ctx.guild.id,))
        page = 0

        while True:
            embed = discord.Embed(title='Select an event',
                                  description='React a number to select an event\nReact :arrow_left: to go backwards a page\nReact :arrow_right: to go forward a page\nReact :new: to create a new event \nReact :eject: to quit',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)
            if len(eventlist):
                embed.add_field(name=f'Available events ({page * 10 + 1}-{min(page * 10 + 10, len(eventlist))}/{len(eventlist)})',
                                value="\n".join(f'{self.EMOJIS[str(i)]} {eventlist[page*10 + i][1]}' for i in range(0, len(eventlist[page*10:page*10+10]))))
            else:
                embed.add_field(name='Available events (0-0/0)',
                                value='None')
            await m.edit(embed=embed)

            try:
                r, u = await self.bot.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                return
            await m.remove_reaction(r, u)

            if (r.emoji == self.EMOJIS["left_arrow"]):
                page -= 1
                page %= ((len(eventlist) - 1) // 10 + 1)
            elif (r.emoji == self.EMOJIS["right_arrow"]):
                page += 1
                page %= ((len(eventlist) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS["new"]:
                await self.makeevent(ctx, m)
                eventlist = await self.executesql('SELECT event_id, name FROM events WHERE server_id = ?', (ctx.guild.id,))
                page = 0
            elif r.emoji == self.EMOJIS['eject']:
                return
            elif r.emoji in self.EMOJIS.values():
                if page*10 + int(r.emoji[0]) < len(eventlist):
                    await self.eventimagemenu(ctx, m, eventlist[page*10 + int(r.emoji[0])][0])
                    eventlist = await self.executesql('SELECT event_id, name FROM events WHERE server_id = ?', (ctx.guild.id,))
                    page = 0

    #Displays a given event's images
    async def eventimagemenu(self, ctx, m, eventid):
        def check(r, u):
            return u == ctx.author and r.message == m

        imagelist = await self.executesql('SELECT image_id, text FROM images WHERE event_id = ?', (eventid,))
        page = 0

        while True:
            embed = discord.Embed(title='Event Wizard - Select an image',
                                  description='React a number to select an image\nReact :arrow_left: to go backwards a page\nReact :arrow_right: to go forward a page\nReact :new: to add a new image\nReact :record_button: to edit event\nReact :eject: to quit',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)
            if len(imagelist):
                embed.add_field(name=f'Available images ({page * 10 + 1}-{min(page * 10 + 10, len(imagelist))}/{len(imagelist)})',
                                value="\n".join(f'{self.EMOJIS[str(i)]} {imagelist[page*10 + i][1]}' for i in range(0, len(imagelist[page*10:page*10+10]))))
            else:
                embed.add_field(name='Available images (0-0/0)',
                                value='None')
            await m.edit(embed=embed)

            try:
                r, u = await self.bot.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                return
            await m.remove_reaction(r, u)

            if (r.emoji == self.EMOJIS["left_arrow"]):
                page -= 1
                page %= ((len(imagelist) - 1) // 10 + 1)
            elif (r.emoji == self.EMOJIS["right_arrow"]):
                page += 1
                page %= ((len(imagelist) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS["new"]:
                await self.makeimage(ctx, m, eventid)
                imagelist = await self.executesql('SELECT image_id, text FROM images WHERE event_id = ?', (eventid,))
            elif r.emoji == self.EMOJIS['record_button']:
                await self.editeventmenu(ctx, m, eventid)
            elif r.emoji == self.EMOJIS['eject']:
                return
            elif r.emoji in self.EMOJIS.values():
                if page*10 + int(r.emoji[0]) < len(imagelist):
                    await self.imagemenu(ctx, m, imagelist[page*10 + int(r.emoji[0])][0])
                    imagelist = await self.executesql('SELECT image_id, text FROM images WHERE event_id = ?', (eventid,))
                    page = 0

    #Edit a given event's variables
    async def editeventmenu(self, ctx, m, eventid):
        def check(r, u):
            return u == ctx.author and r.message == m

        event = await self.executesql('SELECT emoji, cooldown, name FROM events WHERE event_id = ?', (eventid,))

        while True:
            embed = discord.Embed(title=f'Event Wizard - Edit {event[0][2]}',
                                  description='React :zero: to change event name\nReact :one: to change event cooldown\nReact :two: to change event emoji\nReact :record_button: to get an album of all of this event\'s images\nReact :asterisk: to delete event\nReact :eject: to quit',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)
            embed.add_field(name='Cooldown', value=f'{event[0][1]}s')
            embed.add_field(name='Emoji', value=event[0][0])
            await m.edit(embed=embed)

            try:
                r, u = await self.bot.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                return
            await m.remove_reaction(r, u)

            if r.emoji == self.EMOJIS['0']:
                newname = await self.makename(ctx, m)
                if newname:
                    await self.executesql('UPDATE events SET name = ? WHERE event_id = ?', (newname, eventid))
                    event = await self.executesql('SELECT emoji, cooldown, name FROM events WHERE event_id = ?', (eventid,))
            elif r.emoji == self.EMOJIS['1']:
                newcd = await self.makecooldown(ctx, m)
                if newcd:
                    await self.executesql('UPDATE events SET cooldown = ? WHERE event_id = ?', (newcd, eventid))
                    event = await self.executesql('SELECT emoji, cooldown, name FROM events WHERE event_id = ?', (eventid,))
            elif r.emoji == self.EMOJIS['2']:
                newemoji = await self.make_emoji(ctx, m)
                if newemoji:
                    await self.executesql('UPDATE events SET emoji = ? WHERE event_id = ?', (newemoji, eventid))
                    event = await self.executesql('SELECT emoji, cooldown, name FROM events WHERE event_id = ?', (eventid,))
            elif r.emoji == self.EMOJIS['asterisk']:
                await self.delete_event(ctx, m, eventid)
                return
            elif r.emoji == self.EMOJIS['eject']:
                return

    #Edit a given image's variables
    async def imagemenu(self, ctx, m, imageid):
        def check(r, u):
            return u == ctx.author and r.message == m

        image = await self.executesql('SELECT i.text, i.url, i.event_id, r.points_first, r.points_second FROM images i INNER JOIN rarities r USING (rarity_id) WHERE (i.image_id = ?)', (imageid,))

        while True:
            embed = discord.Embed(title=f'Event Wizard - {image[0][0]}',
                                  description='React :zero: to change the name\nReact :one: to change the image\nReact :two: to change the rarity\nReact :asterisk: to delete the image\nReact :eject: to go back',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)
            embed.add_field(name='Points First', value=image[0][3])
            embed.add_field(name='Points On Repeat', value=image[0][4])
            embed.set_image(url=image[0][1])

            await m.edit(embed=embed)

            try:
                r, u = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            except asyncio.TimeoutError:
                return

            await m.remove_reaction(r, u)

            if r.emoji == self.EMOJIS['0']:
                newname = await self.maketext(ctx, m)
                if newname:
                    await self.executesql('UPDATE images SET text = ? WHERE image_id = ?', (newname, imageid))
                    image = await self.executesql('SELECT i.text, i.url, i.event_id, r.points_first, r.points_second FROM images i INNER JOIN rarities r USING (rarity_id) WHERE (i.image_id = ?)', (imageid,))
            elif r.emoji == self.EMOJIS['1']:
                newimage = await self.makeimgurimage(ctx, m, image[0][0])
                if newimage:
                    await self.executesql('UPDATE images SET (url, imgur_id) VALUES (?, ?) WHERE image_id = ?', (newimage['data']['link'], newimage['data']['deletehash'], imageid))
                    image = await self.executesql('SELECT i.text, i.url, i.event_id, r.points_first, r.points_second FROM images i INNER JOIN rarities r USING (rarity_id) WHERE (i.image_id = ?)', (imageid,))
            elif r.emoji == self.EMOJIS['2']:
                newtier = await self.chooserarity(ctx, m, image[0][2])
                if newtier:
                    await self.executesql('UPDATE images SET (rarity_id) VALUES (?)', (newtier,))
                    image = await self.executesql('SELECT i.text, i.url, i.event_id, r.points_first, r.points_second FROM images i INNER JOIN rarities r USING (rarity_id) WHERE (i.image_id = ?)', (imageid,))
            elif r.emoji == self.EMOJIS['eject']:
                return
            elif r.emoji == self.EMOJIS['asterisk']:
                await self.deleteimage(ctx, m, imageid)
                return

#
#
# ------------------- SETTERS ------------------- #
#
#

    async def makeevent(self, ctx, m):
        name = await self.makename(ctx, m)

        if not name:
            return

        emoji = await self.make_emoji(ctx, m)

        if not emoji:
            return

        cooldown = await self.makecooldown(ctx, m)

        if not cooldown:
            return

        await self.executesql('INSERT INTO events (server_id, emoji, cooldown, system_id, name) VALUES (?, ?, ?, ?, ?)', (ctx.guild.id, emoji, cooldown, 1, name))

    async def makeimage(self, ctx, m, eventid):
        text = await self.maketext(ctx, m)

        if not text:
            return

        imgurupload = await self.makeimgurimage(ctx, m, text)

        if not imgurupload:
            return

        rarityid = await self.chooserarity(ctx, m, eventid)

        if not rarityid:
            return

        await self.executesql('INSERT INTO images (event_id, text, url, rarity_id, imgur_id) VALUES (?, ?, ?, ?, ?)', (eventid, text, imgurupload['data']['link'], rarityid, imgurupload['data']['deletehash']))

#
#
# ------------------- EVENT ELEMENT SETTERS ------------------- #
#
#

    async def makename(self, ctx, m):
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        embed = discord.Embed(title='Event Wizard - Event Name',
                              description='Please reply the name of your event\nWait 60s to cancel',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        await m.edit(embed=embed)

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            return

        await msg.delete()

        return msg.content

    async def make_emoji(self, ctx, m):
        def check(r, u):
            return u == ctx.author and r.message == m

        embed = discord.Embed(title='Event Wizard - Event Emoji',
                              description='Please react the emoji you would like this event to use\n**Please don\'t use emojis from other servers as I cannot use them!**\nWait 60s to go back',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        await m.edit(embed=embed)

        while True:
            try:
                r, u = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            except asyncio.TimeoutError:
                return
            await m.remove_reaction(r, u)

            if type(r.emoji) == discord.PartialEmoji:
                embed.description = 'Please only use emojis from this server!\nPlease react a new emoji, or wait 60s to go back'
                await m.edit(embed=embed)
            else:
                return str(r.emoji)

    async def makecooldown(self, ctx, m):
        def check(msg):
            return msg.author == ctx.author and msg.channel == m.channel

        embed = discord.Embed(title='Event Wizard - Cooldown',
                              description='Please reply the minimum time gap between images in seconds\n**This number has to be longer than 60s**\nWait 60s to go back',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        await m.edit(embed=embed)

        while True:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)
                await msg.delete()
                cd = int(msg.content)
            except ValueError:
                cd = None
            except asyncio.TimeoutError:
                return

            if cd < 60:
                embed.description = 'Please reply with a number greater or equal to 60, wait 60s to go back'
                await m.edit(embed=embed)
            elif cd is None:
                embed.description = 'Please reply with a number!\nWait 60s to go back'
                await m.edit(embed=embed)
            else:
                return cd

#
#
# ------------------- IMAGE ELEMENT SETTERS ------------------- #
#
#

    async def maketext(self, ctx, m):
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        embed = discord.Embed(title='Event Wizard - Image Name',
                              description='Please reply the name of this image\nWait 60s to cancel',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        await m.edit(embed=embed)

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            return

        await msg.delete()

        return msg.content

    async def makeimgurimage(self, ctx, m, name):
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel
        def reaction_check(r, u):
            return r.message == m and u == ctx.author and r.emoji == self.EMOJIS['eject']

        embed = discord.Embed(title='Event Wizard - Image',
                              description='Please reply with the image you would like\n**I accept both image uploads or image urls**\n**If using a url, please make sure the url ends with `.png`, `.jp(e)g`, or `.gif`**\nWait 60s to cancel',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        await m.edit(embed=embed)

        while True:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                return

            await msg.delete()

            imageurl = await self.getimageurl(msg)

            if not imageurl:
                embed.description = 'Please make sure your link ends with `.png`, `.jp(e)g`, or `.gif`'
                await m.edit(embed=embed)
            else:
                break

        imgurdata = await self.imgurupload(imageurl, name)
        imgurstatus = imgurdata['status']

        if imgurstatus != 200:
            if imgurstatus == 400:
                embed.description = 'Image not accepted, please make sure you linked a valid image'
            elif imgurstatus == 500:
                embed.description = 'Unexpected Imgur Error - please try again later'

            embed.description += '\nWait 60s, or react :eject: to go back'
            await m.edit(embed=embed)

            while True:
                try:
                    r, u = await self.bot.wait_for('reaction_add', check=reaction_check, timeout=60)
                except asyncio.TimeoutError:
                    return

                await m.remove_reaction(r, u)
                return

        return imgurdata

    async def chooserarity(self, ctx, m, eventid):
        def check(r, u):
            return r.message == m and u == ctx.author and r.emoji in list(self.EMOJIS.values())[:10]

        tiers = await self.executesql('SELECT r.rarity_id, r.rarity_name FROM rarities r INNER JOIN events e USING (system_id) WHERE e.event_id = ?', (eventid,))
        page = 0

        while True:
            embed = discord.Embed(title='Event Wizard - Image Rarity',
                                  description='React a number to select a tier',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)
            embed.add_field(name=f'Available Tiers ({page * 10 + 1}-{min(page * 10 + 10, len(tiers))}/{len(tiers)})',
                            value="\n".join(f'{self.EMOJIS[str(i)]} {tiers[page*10 + i][1]}' for i in range(0, len(tiers[page*10:page*10+10]))))
            await m.edit(embed=embed)

            try:
                r, u = await self.bot.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                return
            await m.remove_reaction(r, u)

            if (r.emoji == self.EMOJIS["left_arrow"]):
                page -= 1
                page %= ((len(tiers) - 1) // 10 + 1)
            elif (r.emoji == self.EMOJIS["right_arrow"]):
                page += 1
                page %= ((len(tiers) - 1) // 10 + 1)
            elif r.emoji in self.EMOJIS.values():
                if page*10 + int(r.emoji[0]) < len(tiers):
                    return tiers[page*10 + int(r.emoji[0])][0]

#
#
# ------------------- SETTER SUPPORT ------------------- #
#
#

    async def getimageurl(self, message: discord.Message):
        image = [image for image in message.attachments if 'image' in image.content_type]

        if len(image):
            return image[0].url
        elif len(message.embeds):
            for embed in message.embeds:
                if embed.image is not discord.Embed.Empty:
                    return message.content
        else:
            return

    async def imgurupload(self, url, name):
        headers = {'Authorization': 'Client-ID ' + IMGUR_ID}
        payload = {'image': url,
                   'type': 'base64',
                   'title': name}

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url='https://api.imgur.com/3/image', json=payload) as r:
                return await r.json()

#
#
# ------------------- RARITY SYSTEM MENUS ------------------- #
#
#

    @commands.command(name='raritywizard', aliases=['rw'], hidden=True)
    @commands.check(rarityWizardCheck)
    async def raritywizard(self, ctx):
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        systems = await self.executesql('SELECT * FROM rarity_systems')

        embed = discord.Embed(title='Rarity Systems',
                              description='\n'.join(f'{systems[i][0]}. {systems[i][1]}' for i in range(0, len(systems))))
        m = await ctx.send(embed=embed)

        while True:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)
                await msg.delete()
                if msg.content.lower() in ['new', 'n']:
                    await self.makesystem(ctx, m)
                    systems = await self.executesql('SELECT * FROM rarity_systems')
                    embed.description = '\n'.join(f'{systems[i][0]}. {systems[i][1]}' for i in range(0, len(systems)))
                    await m.edit(embed=embed)
                elif msg.content.lower() in ['back', 'b']:
                    return
                else:
                    i = int(msg.content)
                    await self.systemmenu(ctx, m, systems[i-1][0])
                    systems = await self.executesql('SELECT * FROM rarity_systems')
                    embed.description = '\n'.join(f'{systems[i][0]}. {systems[i][1]}' for i in range(0, len(systems)))
                    await m.edit(embed=embed)
            except ValueError:
                await ctx.send('Please enter a number or `new`')
            except IndexError:
                await ctx.send('List index out of range')
            except asyncio.TimeoutError:
                await m.delete()
                return

    async def systemmenu(self, ctx, m, sysid):
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        rarities = await self.executesql('SELECT rarity_id, rarity_name FROM rarities WHERE system_id = ?', (sysid,))

        while True:
            embed = discord.Embed(title='System Menu',
                                  description='\n'.join(f'{i + 1}. {rarities[i][1]}' for i in range(0, len(rarities))))
            await m.edit(embed=embed)

            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)
                await msg.delete()
                if msg.content.lower() in ['new', 'n']:
                    await self.maketier(ctx, m, sysid)
                    rarities = await self.executesql('SELECT rarity_id, rarity_name FROM rarities WHERE system_id = ?', (sysid,))
                elif msg.content.lower() in ['delete', 'del', 'd']:
                    await self.executesql('DELETE FROM rarity_systems WHERE system_id = ?', (sysid,))
                    return
                elif msg.content.lower() in ['back', 'b']:
                    return
                else:
                    n = (int(msg.content))
                    await self.tiermenu(ctx, m, rarities[n-1][0])
                    rarities = await self.executesql('SELECT rarity_id, rarity_name FROM rarities WHERE system_id = ?', (sysid,))
            except asyncio.TimeoutError:
                return
            except IndexError:
                await ctx.send('List index out of range')
            except ValueError:
                await ctx.send('Please enter a number, `new`, or `delete`')

    async def tiermenu(self, ctx, m, rarityid):
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        rarityinfo = await self.executesql('SELECT system_id, rarity_name, chance, points_first, points_second FROM rarities WHERE rarity_id = ?', (rarityid,))

        while True:
            embed = discord.Embed(title=f'{rarityinfo[0][1]} Menu')
            embed.add_field(name='Chance', value=f'{rarityinfo[0][2]}%', inline=False)
            embed.add_field(name='Points First', value=rarityinfo[0][3], inline=True)
            embed.add_field(name='Points Repeat', value=rarityinfo[0][4], inline=True)

            await m.edit(embed=embed)

            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)
                await msg.delete()
                if msg.content.lower() in ['points', 'p']:
                    p = await self.makepoints(ctx, m)
                    if p:
                        await self.executesql('UPDATE rarities SET (points_first, points_second) VALUES (?, ?) WHERE rarity_id = ?', (p[0], p[1], rarityid))
                        rarityinfo = await self.executesql('SELECT system_id, rarity_name, chance, points_first, points_second FROM rarities WHERE rarity_id = ?', (rarityid,))
                elif msg.content.lower() in ['name', 'n']:
                    name = await self.makerarityname(ctx, m, rarityinfo[0][0])
                    if name:
                        await self.executesql('UPDATE rarities SET rarity_name = ? WHERE rarity_id = ?', (name, rarityid))
                        rarityinfo = await self.executesql('SELECT system_id, rarity_name, chance, points_first, points_second FROM rarities WHERE rarity_id = ?', (rarityid,))
                elif msg.content.lower() in ['chance', 'c']:
                    chance = await self.makechance(ctx, m, rarityinfo[0][0])
                    if chance:
                        await self.executesql('UPDATE rarities SET chance = ? WHERE rarity_id = ?', (chance, rarityid))
                        rarityinfo = await self.executesql('SELECT system_id, rarity_name, chance, points_first, points_second FROM rarities WHERE rarity_id = ?', (rarityid,))
                elif msg.content.lower() in ['delete', 'del', 'd']:
                    await self.executesql('DELETE FROM rarities WHERE rarity_id = ?', (rarityid,))
                    return
                elif msg.content.lower() in ['back', 'b']:
                    return
            except asyncio.TimeoutError:
                return

#
#
# ------------------- RARITY SYSTEM SETTERS ------------------- #
#
#

    async def makesystem(self, ctx, m):
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        embed = discord.Embed(title='New System',
                              description='Please reply name of new system')

        await m.edit(embed=embed)

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            return

        await msg.delete()

        await self.executesql('INSERT INTO rarity_systems (system_name) VALUES (?)', (msg.content,))

    async def maketier(self, ctx, m, sysid):
        name = await self.makerarityname(ctx, m, sysid)

        if not name:
            return

        chance = await self.makechance(ctx, m, sysid)

        if not chance:
            return

        points = await self.makepoints(ctx, m)

        if not points:
            return

        await self.executesql('INSERT INTO rarities (system_id, rarity_name, chance, points_first, points_second) VALUES (?, ?, ?, ?, ?)', (sysid, name, chance, points[0], points[1]))

    async def makerarityname(self, ctx, m, sysid):
        def check(msg):
            return msg.author == ctx.author and msg.channel == m.channel

        usednames = await self.executesql('SELECT lower(rarity_name) FROM rarities WHERE system_id = ?', (sysid,))

        embed = discord.Embed(title='Event Wizard - Rarity Tier',
                              description='Please reply the name of this rarity tier\nWait 60s to go back',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        await m.edit(embed=embed)

        while True:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                return

            await msg.delete()

            if msg.content.lower() in usednames:
                embed.description = 'This rarity tier name is already being used!\nPlease reply a different name, or wait 60s to go back'
                await m.edit(embed=embed)
            else:
                return msg.content

    async def makepoints(self, ctx, m):
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        p = []

        embed = discord.Embed(title='Event Wizard - Rarity Points',
                              description='Please reply with the number of points images in this tier should be worth on first collection')
        await m.edit(embed=embed)

        while True:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)
                await msg.delete()
                points = int(msg.content)
            except ValueError:
                points = None
            except asyncio.TimeoutError:
                return

            if points is None:
                embed.description = 'Please reply with a number'
                await m.edit(embed=embed)
            else:
                p.append(points)
                break

        embed.description='Please reply with the number of points images in this tier should be worth on repeat collection'

        await m.edit(embed=embed)

        while True:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)
                await msg.delete()
                points = int(msg.content)
            except ValueError:
                points = None
            except asyncio.TimeoutError:
                return

            if points is None:
                embed.description = 'Please reply with a number'
                await m.edit(embed=embed)
            else:
                p.append(points)
                return p

    async def makechance(self, ctx, m, sysid = None):
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        if sysid is None:
            chances = 0
        else:
            chances = await self.executesql('SELECT SUM(chance) FROM rarities WHERE system_id = ?', (sysid,))
            chances = chances[0][0]
            if chances is None:
                chances = 0

        embed = discord.Embed(title='Rarity Chance',
                              description=f'Please reply with the likelihood of an image of this rarity class showing\n**Remaining allocation: {100 - chances}%**')
        await m.edit(embed=embed)

        while True:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)
                await msg.delete()
                chance = float(msg.content)
            except ValueError:
                chance = None
            except asyncio.TimeoutError:
                return

            if chance is None:
                embed.description = 'Please reply with a number!'
                await m.edit(embed=embed)
            elif chances + chance > 100:
                embed.description = 'You don\'t have the percentage allocation for this!'
            else:
                return chance

#
#
# ------------------- DELETE ------------------- #
#
#

    async def delete_event(self, ctx, m, eventid):
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        embed = discord.Embed(title='Delete Event?',
                              description='Are you sure you would like to delete this event? [(y)es/(n)o]',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        await m.edit(embed=embed)

        while True:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                return

            await msg.delete()

            if msg.content.lower() in ['y', 'yes']:
                await self.executesql('DELETE FROM events WHERE event_id = ?', (eventid,))
                return
            elif msg.content.lower() in ['n', 'no']:
                return
            else:
                embed.description = 'I could\'t understand that, would you like to delete this event? [(y)es/(n)o]'
                await m.edit(embed=embed)

    async def deleteimage(self, ctx, m, imageid):
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        embed = discord.Embed(title='Delete Image?',
                              description='Are you sure you would like to delete this image? [(y)es/(n)o]',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        await m.edit(embed=embed)

        while True:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                return

            await msg.delete()

            if msg.content.lower() in ['y', 'yes']:
                await self.executesql('DELETE FROM images WHERE image_id = ?', (imageid,))
                return
            elif msg.content.lower() in ['n', 'no']:
                return
            else:
                embed.description = 'I could\'t understand that, would you like to delete this image? [(y)es/(n)o]'
                await m.edit(embed=embed)

#
#
# ------------------- EVENT POSTING ------------------- #
#
#

    @commands.command(name='event', help='start or stop an event')
    async def event(self, ctx, *args):
        def localcheck(r, u):
            return r.message == m and u == ctx.author and (r.emoji == self.EMOJIS['0'] or r.emoji == self.EMOJIS['1'])
        def check(r, u):
            return r.message == m and u == ctx.author

        await ctx.message.delete()

        if len(args):
            if 'stop' in args[0]:
                active = await self.executesql('SELECT active_id FROM active_events WHERE channel_id = ?', (ctx.message.channel.id,))
                if len(active):
                    await self.executesql('DELETE FROM active_events WHERE active_id = ?', (active[0][0],))
                    await self.executesql('DELETE FROM active_posts WHERE active_id = ?', (active[0][0],))
                    await ctx.send('Stopping event')
                else:
                    await ctx.send('There is no event running in this channel!')
                return

            if len(await self.executesql('SELECT active_id FROM active_events WHERE channel_id = ?', (ctx.channel.id,))):
                return await ctx.send('Event already active in this channel!')
            elif 'start' in args[0] and len(args) > 1:
                localevent = await self.executesql('SELECT event_id FROM events e WHERE (server_id = ? AND lower(name) = ?) AND e.event_id NOT IN (SELECT active_id FROM active_events WHERE server_id = ?)', (ctx.guild.id, args[1].lower(), ctx.guild.id))
                globalevent = await self.executesql('SELECT event_id FROM events e WHERE (server_id = 813532137050341407 AND lower(name) = ?) AND e.event_id NOT IN (SELECT active_id FROM active_events WHERE server_id = ?)', (args[1].lower(), ctx.guild.id))
                if not (len(localevent) or len(globalevent)):
                    await ctx.send('Event not found')
                    return
                elif (len(localevent) and len(globalevent)):
                    embed = discord.Embed(title='Event',
                                          description='Multiple events using this name detected\nReact :zero: for the local event\nReact :one: for the global event\nWait 60s to cancel',
                                          colour=ctx.guild.get_member(self.bot.user.id).colour)
                    m = await ctx.send(embed=embed)
                    await m.add_reaction(self.EMOJIS['0'])
                    await m.add_reaction(self.EMOJIS['1'])

                    while True:
                        try:
                            r, u = await self.bot.wait_for('reaction_add', check=localcheck, timeout=60)
                            await m.remove_reaction(r, u)

                            if r.emoji == self.EMOJIS['0']:
                                await self.executesql('INSERT INTO active_events (event_id, server_id, channel_id) VALUES (?, ?, ?)', (localevent[0][0], ctx.guild.id, ctx.channel.id))
                                await m.delete()
                                newid = await self.executesql('SELECT active_id FROM active_events WHERE server_id = ? AND channel_id = ?', (ctx.guild.id, ctx.channel.id))
                                await ctx.send('Starting event...')
                                return await self.eventpost(newid[0][0])
                            else:
                                await self.executesql('INSERT INTO active_events (event_id, server_id, channel_id) VALUES (?, ?, ?)', (globalevent[0][0], ctx.guild.id, ctx.channel.id))
                                await m.delete()
                                newid = await self.executesql('SELECT active_id FROM active_events WHERE server_id = ? AND channel_id = ?', (ctx.guild.id, ctx.channel.id))
                                await ctx.send('Starting event...')
                                return await self.eventpost(newid[0][0])
                        except asyncio.TimeoutError:
                            await m.delete()
                            return
                elif len(localevent):
                    await self.executesql('INSERT INTO active_events (event_id, server_id, channel_id) VALUES (?, ?, ?)', (localevent[0][0], ctx.guild.id, ctx.channel.id))
                    newid = await self.executesql('SELECT active_id FROM active_events WHERE server_id = ? AND channel_id = ?', (ctx.guild.id, ctx.channel.id))
                    await ctx.send('Starting event...')
                    return await self.eventpost(newid[0][0])
                elif len(globalevent):
                    await self.executesql('INSERT INTO active_events (event_id, server_id, channel_id) VALUES (?, ?, ?)', (globalevent[0][0], ctx.guild.id, ctx.channel.id))
                    newid = await self.executesql('SELECT active_id FROM active_events WHERE server_id = ? AND channel_id = ?', (ctx.guild.id, ctx.channel.id))
                    await ctx.send('Starting event...')
                    return await self.eventpost(newid[0][0])
            else:
                if not len(await self.executesql('SELECT active_id FROM active_events WHERE server_id = ? AND event_id = ?', (ctx.guild.id, self.defaultevent))):
                    await self.executesql('INSERT INTO active_events (event_id, server_id, channel_id) VALUES (?, ?, ?)', (self.defaultevent, ctx.guild.id, ctx.channel.id))
                    newid = await self.executesql('SELECT active_id FROM active_events WHERE server_id = ? AND channel_id = ?', (ctx.guild.id, ctx.channel.id))
                    await ctx.send('Starting event...')
                    return await self.eventpost(newid[0][0])
                else:
                    await ctx.send('You already have an event running!')
                    return
        else:
            #if premium server, allow them to choose an event from their made events
            if len(await self.executesql('SELECT server_id FROM premium_users WHERE server_id = ?', (ctx.guild.id,))):
                events = await self.executesql('SELECT event_id, name FROM events e WHERE (server_id = ?) NOT IN (SELECT active_id FROM active_events WHERE server_id = ?)', (ctx.guild.id, ctx.guild.id))
                page = 0

                embed = discord.Embed(title='Event Selection',
                                      description='Loading...',
                                      colour=ctx.guild.get_member(self.bot.user.id).colour)
                m = await ctx.send(embed=embed)

                for e in self.EMOJIS.values():
                    await m.add_reaction(e)

                while True:
                    embed = discord.Embed(title='React a number to select an event',
                                          description='Please choose an event\nReact :arrow_left: to go backwards a page\nReact :arrow_right: to go forward a page',
                                          colour=ctx.guild.get_member(self.bot.user.id).colour)
                    if len(events):
                        embed.add_field(name=f'Available events ({page * 10 + 1}-{min(page * 10 + 10, len(events))}/{len(events)})',
                                        value="\n".join(f'{self.EMOJIS[str(i)]} {events[page*10 + i][1]}' for i in range(0, len(events[page*10:page*10+10]))))
                    else:
                        embed.add_field(name='Available events (0-0/0)',
                                        value='None')
                    await m.edit(embed=embed)

                    try:
                        r, u = await self.bot.wait_for('reaction_add', check=check, timeout=60)
                        await m.remove_reaction(r, u)

                        if (r.emoji == self.EMOJIS["left_arrow"]):
                            page -= 1
                            page %= ((len(events) - 1) // 10 + 1)
                        elif (r.emoji == self.EMOJIS["right_arrow"]):
                            page += 1
                            page %= ((len(events) - 1) // 10 + 1)
                        elif r.emoji == self.EMOJIS['eject']:
                            await m.delete()
                            return
                        elif r.emoji in self.EMOJIS.values():
                            if page*10 + int(r.emoji[0]) < len(events):
                                await m.delete()
                                await self.executesql('INSERT INTO active_events (event_id, server_id, channel_id) VALUES (?, ?, ?)', (events[page*10 + int(r.emoji[0])][0], ctx.guild.id, ctx.channel.id))
                                newid = await self.executesql('SELECT active_id FROM active_events WHERE server_id = ? AND channel_id = ?', (ctx.guild.id, ctx.channel.id))
                                await ctx.send('Starting event...')
                                return await self.eventpost(newid[0][0])
                    except asyncio.TimeoutError:
                        await m.delete()
                        return
                    except ValueError:
                        pass
            #checks if an event is running in server
            elif not len(await self.executesql('SELECT active_id FROM active_events WHERE server_id = ? AND event_id = ?', (ctx.guild.id, self.defaultevent))):
                await self.executesql('INSERT INTO active_events (event_id, server_id, channel_id) VALUES (?, ?, ?)', (self.defaultevent, ctx.guild.id, ctx.channel.id))
                newid = await self.executesql('SELECT active_id FROM active_events WHERE server_id = ? AND channel_id = ?', (ctx.guild.id, ctx.channel.id))
                await ctx.send('Starting event...')
                return await self.eventpost(newid[0][0])
            else:
                await ctx.send('You already have an event running!')
                return

    @commands.command(name='force', hidden=True)
    @commands.is_owner()
    async def forcepost(self, ctx, activeid):
        await ctx.send('Forcing event to post')
        await self.eventpost(activeid)

    async def eventpost(self, activeid):
        activeinfo = await self.executesql('SELECT event_id, server_id, channel_id FROM active_events WHERE active_id = ?', (activeid,))
        eventinfo = await self.executesql('SELECT cooldown, emoji FROM events WHERE event_id = ?', (activeinfo[0][0],))

        await asyncio.sleep(eventinfo[0][0])
        start = time()
        print('starting posting at: ' + str(start))

        while True:
            await asyncio.sleep(5)

            if await Event.checktime(self, start):
                image = await Event.getimage(self, activeinfo[0][0])

                embed = discord.Embed(title=image[1])
                embed.set_image(url=image[2])

                m = await self.bot.get_guild(activeinfo[0][1]).get_channel(activeinfo[0][2]).send(embed=embed)
                await m.add_reaction(eventinfo[0][1])

                await Event.executesql(self, 'REPLACE INTO active_posts (active_id, event_id, image_id, message_id) VALUES (?, ?, ?, ?)', (activeid, activeinfo[0][0], image[0], m.id))
                return

    async def getimage(self, eventid):
        images = []
        while not len(images):
            tier = await Event.getrarity(self, eventid)

            images = await Event.executesql(self, 'SELECT image_id, text, url, rarity_id FROM images WHERE event_id = ? AND rarity_id = ?', (eventid, tier))

        return choice(images)

    async def getrarity(self, eventid):
        rarities = await Event.executesql(self, 'SELECT r.rarity_id, r.chance FROM rarities r INNER JOIN events e USING (system_id) WHERE e.event_id = ?', (eventid,))

        while True:
            r = random() * float(100)
            for chance in rarities:
                if r - chance[1] <= 0:
                    return chance[0]
                else:
                    r -= chance[1]

    async def checktime(self, oldtime):
        newtime = time()
        if random() > pow(0.99, newtime - oldtime):
            return True

#
#
# ------------------- OTHERS ------------------- #
#
#

    async def makeimguralbum(self, eventid):
        imageids = [hash[0] for hash in await self.executesql('SELECT imgur_id FROM images WHERE event_id = ?', (eventid,))]
        eventname = await self.executesql('SELECT name FROM events WHERE event_id = ?', (eventid,))[0][0]
        headers = {'Authorization': 'Client-ID ' + IMGUR_ID}
        payload = {'deletehashes[]': imageids,
                   'title': eventname}

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url='https://api.imgur.com/3/album', json=payload) as r:
                if r.status == 200:
                    r = r.json()

    @commands.command(name='fixflags', hidden=True)
    @commands.is_owner()
    async def fixflags(self, ctx):
        flags = await self.executesql("SELECT image_id, text FROM images WHERE text LIKE '%flag'")
        for flag in flags:
            newstr = f'{flag[1][:-4]} {flag[1][-4:]}'
            await self.executesql('UPDATE images SET text = ? WHERE image_id = ?', (newstr, flag[0]))
        await ctx.send('done')



def setup(bot):
    bot.add_cog(Event(bot))
