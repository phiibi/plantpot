# dressup.py
# unimplemented code for Halloween 2021, mostly will be reused for Halloween 2022

import asyncio
import discord
import pathlib
import random

from aiosqlite import connect
from discord.ext import commands, tasks
from PIL import Image


class DressUp(commands.Cog):
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
        "eject":          "⏏️",
    }

    BODYAREAS = {0: 'background',
                 1: 'back accessories',
                 2: 'hair back',
                 3: 'body',
                 4: 'clothes',
                 5: 'accessories',
                 6: 'hair front',
                 7: 'face accessories',
                 8: 'hair extras'}

    def __init__(self, bot):

        self.bot = bot

        self.setup.start()

    @tasks.loop(count=1)
    async def setup(self):
        await self.executesql("PRAGMA foreign_keys = ON")

        await self.executesql("""CREATE TABLE IF NOT EXISTS pieces (
                    piece_id INTEGER PRIMARY KEY,
                    area TEXT NOT NULL,
                    piece_name TEXT NOT NULL,
                    file_location TEXT NOT NULL,
                    url TEXT NOT NULL)""")

        await self.executesql("""CREATE TABLE IF NOT EXISTS piece_inventory (
                    unique_piece_id INTEGER PRIMARY KEY,
                    piece_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    CONSTRAINT fk_piece FOREIGN KEY (piece_id) REFERENCES pieces(piece_id))""")

        await self.executesql("""CREATE TABLE IF NOT EXISTS piece_setup (
                    unique_set_id INTEGER PRIMARY KEY,
                    piece_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    CONSTRAINT fk_piece FOREIGN KEY (piece_id) REFERENCES pieces(piece_id))""")

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

    @commands.command(name='dressup', help='dress up your very own Halloween plant!')
    @commands.is_owner()
    async def dressup(self, ctx, mode=None):
        if mode is None or mode.lower() == 'post':
            await self.postdressup(ctx)
        elif mode.lower() == 'inventory':
            await self.dressupinventory(ctx)

    async def postdressup(self, ctx):
        filepath = f'./cogs/halloweenimages/{ctx.author.id}'
        userpieces = await self.executesql("""SELECT p.file_location FROM pieces p INNER JOIN piece_setup ps
                                              USING (piece_id) WHERE ps.user_id = ? ORDER BY p.area ASC""")
        self.constructimage(userpieces, pathlib.Path(filepath))
        await ctx.send(file=discord.File(filepath))

    async def dressupinventory(self, ctx):
        def check(r, u):
            return r.message == m and u == ctx.author

        userpieces = await self.executesql("""SELECT p.piece_id, p.area, p.piece_name, p.url 
                                              FROM pieces p INNER JOIN piece_inventories inv USING (piece_id) 
                                              WHERE inv.user_id = ?""", (ctx.author.id,))

        if not len(userpieces):
            return ctx.send("You don't have anything in your inventory! Please retry again once you've collected some pieces of me")

        embed = discord.Embed(title='Dress Up Inventory',
                              description='Loading...',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        m = await ctx.send(embed=embed)

        areas = {[piece[1] for piece in userpieces]}
        areas = list(areas)
        for i in range(len(areas)):
            await m.add_reaction(self.EMOJIS[str(i)])
        await m.add_reaction(self.EMOJIS['eject'])

        while True:
            embed = discord.Embed(title='Dress Up Inventory',
                                  description='Please react a number to select an area\nReact :eject: to quit',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)
            embed.add_field(name='Available Areas',
                            value='\n'.join(f'{self.EMOJIS[str(i)]} {self.BODYAREAS.get(areas[i])}' for i in range(len(areas))))
            await m.edit(embed=embed)

            try:
                r, u = await self.bot.wait_for('reaction_add', timeout=60, check=check)
                await m.remove_reaction(r, u)

                if r.emoji == self.EMOJIS['eject']:
                    await m.delete()
                    return
                elif r.emoji in self.EMOJIS.values() and int(r.emoji[0]) <= len(areas):
                    await self.areainventory(ctx, m, userpieces, areas[int(r.emoji[0])])
            except asyncio.TimeoutError:
                await m.delete()
                return

    async def areainventory(self, ctx, m, pieces, area):
        def check(r, u):
            return r.message == m and u == ctx.author

        areapieces = [piece for piece in pieces if piece[1] == area]

        if (len(m.reactions) - 1) < len(areapieces):
            for i in range(len(areapieces)):
                await m.add_reaction(self.EMOJIS[str(i)])
        while True:
            embed = discord.Embed(title=f'{self.BODYAREAS[area]}',
                                  description='Please react a number to select an item\nReact :eject: to go back',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)
            embed.add_field(name='Available Pieces',
                            value='\n'.join(f'{self.EMOJIS[str(i)]} {areapieces[i][2]}' for i in range(len(areapieces))))

            await m.edit(embed=embed)
            try:
                r, u = await self.bot.wait_for('reaction_add', timeout=60, check=check)
                await m.remove_reaction(r, u)

                if r.emoji == self.EMOJIS['eject']:
                    return
                elif r.emoji in self.EMOJIS.values() and int(r.emoji[0]) <= len(areapieces):
                    await self.pieceinventory(ctx, m, areapieces[int(r.emoji[0])])
            except asyncio.TimeoutError:
                return

    async def pieceinventory(self, ctx, m, piece):
        def check(r, u):
            return r.message == m and u == ctx.author
        imageurl = await self.executesql('SELECT url FROM pieces WHERE piece_id = ?', (piece[0],))
        while True:
            isset = await self.executesql('SELECT * FROM piece_setup WHERE piece_id = ? AND user_id = ?', (piece[0], ctx.author.id))
            embed = discord.Embed(title=f'{piece[2]}',
                                  description='React with :zero: to set this piece\nReact with :eject: to go back',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)
            if len(isset):
                embed.add_field(name='IS SET',
                                value='This piece is currently set on your dress up')
            embed.set_image(url=imageurl[0][0])
            await m.edit(embed=embed)

            try:
                r, u = await self.bot.wait_for('reaction_add', timeout=60, check=check)
                await m.remove_reaction(r, u)

                if r.emoji == self.EMOJIS['eject']:
                    return
                elif r.emoji == self.EMOJIS[0]:
                    if len(isset):
                        await ctx.send('This piece is already set!')
                    else:
                        await self.setpiece(ctx, piece)
            except asyncio.TimeoutError:
                return

    async def setpiece(self, ctx, piece):
        areaset = await self.executesql("""SELECT ps.unique_set_id FROM piece_setup ps INNER JOIN pieces p
                                           USING (piece_id) WHERE ps.user_id = ? AND p.area = ?""", (ctx.author.id, piece[1]))
        if len(areaset):
            await self.executesql('UPDATE piece_setup SET piece_id = ? WHERE unique_set_id = ?', (piece[0], areaset[0]))
        else:
            await self.executesql('INSERT INTO piece_setup (piece_id, user_id) VALUES (?, ?)', (piece[0], ctx.author.id))

        await ctx.send('Piece set!')

    async def giveuniquepiece(self, userid):
        if random.random < 0.015:
            userpieces = await self.executesql("SELECT * FROM piece_inventory WHERE user_id = ?", (userid,))
            if not len(userpieces):
                unique_pieces = await self.executesql("""SELECT piece_id, piece_name
                                         FROM pieces WHERE piece_id NOT IN (
                                         SELECT piece_id FROM piece_inventory WHERE
                                         user_id = ?)""", (userid,))

                piece = random.choice(unique_pieces)

            else:
                piece = [0, "Plant Base"]
            await self.executesql("INSERT INTO piece_inventory (piece_id, user_id) VALUES (?, ?)", (piece[0], userid))
            return piece

    def constructimage(self, pieces, path):
        base = Image.open(pieces[0], 'r')
        for i in range(len(pieces)):
            if i:
                base.paste(pieces[i][0], 'r')
        base.show()
        base.save(path)

def setup(bot):
    bot.add_cog(DressUp(bot))