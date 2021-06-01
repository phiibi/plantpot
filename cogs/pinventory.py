#inventory.py


import asyncio
import discord

from math import ceil
from operator import itemgetter
from discord.ext import commands, tasks
from aiosqlite import connect


class PrideInventory(commands.Cog):
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

    CONTROL_EMOJIS = ['\U00002B05', '\U000027A1']

    def __init__(self, bot):
        self.bot = bot

        self.setup.start()

    @tasks.loop(count=1)
    async def setup(self):
        await self.executesql("PRAGMA foreign_keys = ON")

        await self.executesql("""CREATE TABLE IF NOT EXISTS inventories (
                    unique_item_id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    image_id INTEGER NOT NULL,
                    event_id INTEGER NOT NULL,
                    server_id INTEGER NOT NULL,
                    count INTEGER NOT NULL,
                    CONSTRAINT fk_image FOREIGN KEY (image_id) REFERENCES images(image_id),
                    CONSTRAINT fk_event FOREIGN KEY (event_id) REFERENCES events(event_id))""")

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

    @commands.command(name='prideinventory', help='displays your inventory', aliases=['inv'])
    async def inventoryselect(self, ctx, *, eventname=None):
        def check(r, u):
            return u == ctx.author and r.message == m

        inventories = await self.executesql('SELECT DISTINCT e.event_id, e.name FROM events e INNER JOIN inventories i USING (event_id) WHERE ((i.user_id = ?) AND (i.server_id = ?))', (ctx.author.id, ctx.guild.id))
        page = 0

        embed = discord.Embed(title='Inventory Menu',
                              description='Loading...',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        m = await ctx.send(embed=embed)

        eventname = 'pride'

        if eventname is not None:
            checklb = await self.executesql('SELECT DISTINCT lb.event_id, lb.score FROM leaderboards lb INNER JOIN events e USING (event_id) WHERE lb.server_id = ? AND lb.user_id = ? AND lower(e.name) = ?', (ctx.guild.id, ctx.author.id, eventname.lower()))
            if len(checklb):
                return await self.displayposition(ctx, m, checklb[0][0], checklb[0][1])

        for e in self.EMOJIS.values():
            await m.add_reaction(e)

        while True:
            embed = discord.Embed(title='Inventory Menu',
                                  description='React a number to select an inventory\nReact :arrow_left: to go backwards a page\nReact :arrow_right: to go forward a page\nReact :eject: to quit',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)

            if len(inventories):
                embed.add_field(name=f'Available inventories ({page * 10 + 1}-{min(page * 10 + 10, len(inventories))}/{len(inventories)})',
                                value="\n".join(f'{self.EMOJIS[str(i)]} {inventories[page*10 + i][1]}' for i in range(0, len(inventories[page*10:page*10+10]))))
            else:
                embed.add_field(name='Available inventories (0-0/0)',
                                value='None')
            await m.edit(embed=embed)

            try:
                r, u = await self.bot.wait_for("reaction_add", check=check, timeout=60)
            except asyncio.TimeoutError:
                return
            await m.remove_reaction(r, u)

            if r.emoji == self.EMOJIS["left_arrow"]:
                page -= 1
                page %= ((len(inventories) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS["right_arrow"]:
                page += 1
                page %= ((len(inventories) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS["eject"]:
                return await m.delete()
            elif r.emoji in self.EMOJIS.values():
                if page*10 + int(r.emoji[0]) < len(inventories):
                    return await self.sortmenu(ctx, m, inventories[page*10 + int(r.emoji[0])][0])

    async def sortmenu(self, ctx, m, eventid):
        def check(r, u):
            return r.message == m and u == ctx.author

        embed = discord.Embed(title='Inventory Menu',
                              description= 'Please react with a number based on how you would like your inventory sorted\nReact with :zero: for pick up order: **oldest - newest**\nReact with :one: for pick up order: **newest - oldest**\nReact with :two: for by alphabetical: **A - Z**\nReact with :three: for by alphabetical: **Z - A**\nReact with :four: for quantity: **high - low**\nReact with :five: for quantity: **low - high**\nReact with :six: for rarity: **high - low**\nReact with :seven: for rarity: **low - high**\n',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        await m.edit(embed=embed)

        while True:
            try:
                r, u = await self.bot.wait_for('reaction_add', check=check, timeout=60)
                await m.remove_reaction(r, u)

                if r.emoji == self.EMOJIS["0"]:
                    return await self.inventory(ctx, m, await self.sortpickup(ctx.author.id, eventid, ctx.guild.id))
                elif r.emoji == self.EMOJIS["1"]:
                    return await self.inventory(ctx, m, await self.sortpickup(ctx.author.id, eventid, ctx.guild.id, True))
                elif r.emoji == self.EMOJIS["2"]:
                    return await self.inventory(ctx, m, await self.sortalphabetical(ctx.author.id, eventid, ctx.guild.id))
                elif r.emoji == self.EMOJIS["3"]:
                    return await self.inventory(ctx, m, await self.sortalphabetical(ctx.author.id, eventid, ctx.guild.id, True))
                elif r.emoji == self.EMOJIS["4"]:
                    return await self.inventory(ctx, m, await self.sortquantity(ctx.author.id, eventid, ctx.guild.id))
                elif r.emoji == self.EMOJIS["5"]:
                    return await self.inventory(ctx, m, await self.sortquantity(ctx.author.id, eventid, ctx.guild.id, True))
                elif r.emoji == self.EMOJIS["6"]:
                    return await self.inventory(ctx, m, await self.sortrarity(ctx.author.id, eventid, ctx.guild.id))
                elif r.emoji == self.EMOJIS["7"]:
                    return await self.inventory(ctx, m, await self.sortrarity(ctx.author.id, eventid, ctx.guild.id, True))
            except asyncio.TimeoutError:
                return await m.delete()

    async def inventory(self, ctx, m, items):
        def check(r, u):
            return r.message == m and r.emoji in self.CONTROL_EMOJIS and u == ctx.author

        await m.clear_reactions()

        embed = discord.Embed(title='Your Inventory',
                              description='Loading...',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        await m.edit(embed=embed)

        await m.add_reaction(self.CONTROL_EMOJIS[0])
        await m.add_reaction(self.CONTROL_EMOJIS[1])

        page = 0
        if len(items) >= 200:
            perpage = 25
        else:
            perpage = 10

        embed.set_thumbnail(url=ctx.author.avatar_url_as())
        while True:
            embed.description = '\n'.join(f'{i + 1}.\U00002800 {items[i][1]}x **{items[page * perpage + i][0]}**' for i in range(0, len(items[page * perpage:page * perpage + perpage])))
            embed.set_footer(text=f'Page {page + 1}/{ceil(len(items)/perpage)}')

            await m.edit(embed=embed)

            try:
                r, u = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            except asyncio.TimeoutError:
                await m.delete()
                return
            await m.remove_reaction(r, u)

            if r.emoji == self.CONTROL_EMOJIS[0]:
                page -= 1
                page %= ((len(items) - 1) // perpage + 1)
            elif r.emoji == self.CONTROL_EMOJIS[1]:
                page += 1
                page %= ((len(items) - 1) // perpage + 1)

    @commands.command(name='pridegive', help='gives another user an item')
    async def give(self, ctx, user: discord.Member, *, item):
        def check(m):
            return m.author == user and m.channel == ctx.channel

        if user == self.bot.user:
            return await ctx.send('thank you but i could never accept this gift')
        elif user == ctx.message.author:
            return await ctx.send('you can\'t give yourself something!')

        iteminfo = await self.executesql('SELECT image_id, event_id FROM images WHERE lower(text) = ?', (item.lower(),))

        if not len(iteminfo):
            return await ctx.send(f'couldn\'t find {item}')
        elif await self.removeitem(ctx.author.id, ctx.guild.id, iteminfo[0][0], 1):
            msg = await ctx.send(f'{user.mention}! {ctx.author.mention} wants to give you {item}, do you accept? [(y)es/(n)o]')

            while True:
                try:
                    m = await self.bot.wait_for('message', check=check, tiumeout=60)
                    if m.content.lower() in ['y', 'yes']:
                        await self.additem(user.id, ctx.guild.id, iteminfo[0][1], iteminfo[0][0], 1)
                        return await msg.edit(content=f'congratulations {user.mention}, you\'re the proud new owner of {item}')
                    elif m.content.lower() in ['n', 'no']:
                        await self.additem(ctx.author.id, ctx.guild.id, iteminfo[0][1], iteminfo[0][0], 1)
                        return await msg.edit(content=f'uh oh, {user.mention} doesn\'t want {ctx.author.mention}\'s {item}')
                except asyncio.TimeoutError:
                    return await msg.edit(content=f'uh oh, {user.mention} didn\'t respond in time, please try again when they\'re not busy')
        else:
            return await ctx.send(f'you don\'t have any {image}s to give out!')


#
#
# ------------------- HELPERS ------------------- #
#
#

    async def sortalphabetical(self, userid, eventid, serverid, reverse=False):
        items = await self.executesql('SELECT im.text, inv.count FROM inventories inv INNER JOIN images im USING (image_id) WHERE (im.event_id = ? AND inv.user_id = ? AND inv.server_id = ?)', (eventid, userid, serverid))
        items.sort(key=itemgetter(0), reverse=reverse)
        return items

    async def sortquantity(self, userid, eventid, serverid, reverse=False):
        items = await self.executesql('SELECT im.text, inv.count FROM inventories inv INNER JOIN images im USING (image_id) WHERE (im.event_id = ? AND inv.user_id = ? AND inv.server_id = ?)', (eventid, userid, serverid))
        items.sort(key=itemgetter(1), reverse=reverse)
        return items

    async def sortpickup(self, userid, eventid, serverid, reverse=False):
        items = await self.executesql('SELECT im.text, inv.count FROM inventories inv INNER JOIN images im USING (image_id) WHERE (im.event_id = ? AND inv.user_id = ? AND inv.server_id = ?)', (eventid, userid, serverid))
        if reverse:
            items.reverse()
        return items

    async def sortrarity(self, userid, eventid, serverid, reverse=False):
        items = await self.executesql('SELECT im.text, inv.count, r.chance FROM inventories inv INNER JOIN images im USING (image_id) INNER JOIN rarities r ON (im.rarity_id = r.rarity_id) WHERE (im.event_id = ? AND inv.user_id = ? AND inv.server_id = ?) ORDER BY r.chance ASC', (eventid, userid, serverid))
        if reverse:
            items.reverse()
        return items

    async def additem(self, userid, serverid, eventid, imageid, count):
        item = await self.executesql('SELECT unique_item_id, count FROM inventories WHERE (user_id = ? AND image_id = ? AND server_id = ?)', (userid, imageid, serverid))
        if len(item):
            await self.executesql('UPDATE inventories SET count = ? WHERE unique_item_id = ?', (item[0][1] + count, item[0][0]))
        else:
            await self.executesql('INSERT INTO inventories (user_id, server_id, event_id, image_id, count) VALUES (?, ?, ?, ?, ?)', (userid, serverid, eventid, imageid, count))

    async def removeitem(self, userid, serverid, imageid, count):
        item = await self.executesql('SELECT unique_item_id, count FROM inventories WHERE (user_id = ? AND server_id = ? AND image_id = ?)', (userid, serverid, imageid))
        if len(item):
            item = item[0]
            if not (item[1] - count):
                await self.executesql('DELETE FROM inventories WHERE unique_item_id = ?', (item[0],))
                return True
            elif item[1] > count:
                await self.executesql('UPDATE inventories SET count = ? WHERE unique_item_id = ?', (item[1] - count, item[0]))
                return True
            else:
                return False
        else:
            return False

    @give.error
    async def giveerror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
            await ctx.send("please format as `.give [user] [item]`")

def setup(bot):
    bot.add_cog(PrideInventory(bot))