#crafting.py

import asyncio
import discord

from discord.ext import commands, tasks
from aiosqlite import connect
from cogs.inventory import Inventory
from cogs.leaderboard import Leaderboard

class Crafting(commands.Cog):
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

    MENU_EMOJIS = {
        "0":              "0️⃣",
        "1":              "1️⃣",
        "2":              "2️⃣"}

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

    @commands.command(name='craft', help='craft new items, use .craftinghelp for more help')
    async def craft(self, ctx, type=None):
        def check(r, u):
            return u == ctx.author and r.message == m

        if type is not None:
            if type.lower() in ['flag']:
                return await self.craftflag(ctx)
            elif type.lower() in ['cutout']:
                return await self.craftcutout(ctx)
            elif type.lower() in ['help']:
                return await self.crafthelp(ctx)

        embed = discord.Embed(title='Crafting Menu',
                              description='Please react a number based on what you would like to see\nReact :zero: for flag crafting\nReact :one: for cutout crafting\nReact :two: for help',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        m = await ctx.send(embed=embed)

        for e in self.MENU_EMOJIS.values():
            await m.add_reaction(e)

        while True:

            try:
                r, u = await self.bot.wait_for("reaction_add", check=check, timeout=60)
            except asyncio.TimeoutError:
                return await m.delete()
            await m.remove_reaction(r, u)

            if r.emoji == self.EMOJIS['0']:
                return await self.craftflag(ctx, m)
            elif r.emoji == self.EMOJIS['1']:
                return await self.craftcutout(ctx, m)
            elif r.emoji == self.EMOJIS['2']:
                return await self.crafthelp()

    async def craftflag(self, ctx, m=None):
        def check(r, u):
            return u == ctx.author and r.message == m

        flags = await self.executesql("SELECT image_id, text, event_id, url FROM images WHERE text LIKE '%flag' ORDER BY lower(text)", ())
        page = 0
        userstripes = await self.executesql("SELECT i.image_id, inv.count FROM inventories inv INNER JOIN images i USING (image_id) WHERE (inv.user_id = ? AND inv.server_id = ? AND i.text LIKE '%stripe')", (ctx.author.id, ctx.guild.id))

        temp = 22
        for stripe in userstripes:
            if stripe[1] >= 2:
                temp -= 2
            else:
                temp -= stripe[1]

        if temp:
            if m is not None:
                await m.delete()
            return await ctx.send(f"You don't have enough stripes to craft a flag, please try again when you have a flag's worth\nRemaining stripes: {temp}")

        embed = discord.Embed(title='Crafting Menu',
                              description='Loading...',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        if m is None:
            m = await ctx.send(embed=embed)
        else:
            await m.clear_reactions()
            await m.edit(embed=embed)

        for e in self.EMOJIS.values():
            await m.add_reaction(e)

        while True:
            embed = discord.Embed(title='Crafting Menu',
                                  description='React to craft a flag\nReact :arrow_left: to go backwards a page\nReact :arrow_right: to go forward a page\nReact :eject: to quit',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)

            embed.add_field(name=f'Available flags ({page * 10 + 1}-{min(page * 10 + 10, len(flags))}/{len(flags)})',
                            value="\n".join(f'{self.EMOJIS[str(i)]} {flags[page*10 + i][1]}' for i in range(0, len(flags[page*10:page*10+10]))))
            await m.edit(embed=embed)

            try:
                r, u = await self.bot.wait_for("reaction_add", check=check, timeout=60)
            except asyncio.TimeoutError:
                return await m.delete()
            await m.remove_reaction(r, u)

            if r.emoji == self.EMOJIS["left_arrow"]:
                page -= 1
                page %= ((len(flags) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS["right_arrow"]:
                page += 1
                page %= ((len(flags) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS["eject"]:
                return await m.delete()
            elif r.emoji in self.EMOJIS.values():
                if page*10 + int(r.emoji[0]) < len(flags):
                    await m.delete()
                    return await self.giveflag(ctx, userstripes, flags[page*10 + int(r.emoji[0])])

    async def craftcutout(self, ctx, m=None):
        def check(r, u):
            return u == ctx.author and r.message == m
        userflags = await self.executesql("SELECT i.image_id, inv.count, i.text FROM inventories inv INNER JOIN images i USING (image_id) WHERE (inv.user_id = ? AND inv.server_id = ? AND i.text LIKE '%flag')", (ctx.author.id, ctx.guild.id))
        usercutouts = await self.executesql("SELECT i.image_id, inv.count, i.text FROM inventories inv INNER JOIN images i USING (image_id) WHERE (inv.user_id = ? AND inv.server_id = ? AND i.text LIKE '%cutout')", (ctx.author.id, ctx.guild.id))

        if not len(userflags):
            if m is not None:
                await m.delete()
            return await ctx.send("You don't have any flags, please try again when you have a flag")
        elif not len(usercutouts):
            if m is not None:
                await m.delete()
            return await ctx.send("You don't have any cutouts, please try again when you have a cutout")

        embed = discord.Embed(title='Crafting Menu',
                              description='React to choose a shape',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        embed.add_field(name='Available shapes',
                        value="\n".join(f'{self.MENU_EMOJIS[str(i)]} {usercutouts[i][2][:-7]}' for i in range(0, len(usercutouts))))

        if m is not None:
            await m.clear_reactions()
            await m.edit(embed=embed)
        else:
            m = await ctx.send(embed=embed)

        for i in range(len(usercutouts)):
            await m.add_reaction(list(self.MENU_EMOJIS.values())[i])

        while True:
            try:
                r, u = await self.bot.wait_for("reaction_add", check=check, timeout=60)
            except asyncio.TimeoutError:
                return await m.delete()
            await m.remove_reaction(r, u)

            if r.emoji in self.MENU_EMOJIS.values():
                type = usercutouts[int(r.emoji[0])][2][:-7]
                break

        embed = discord.Embed(title='Crafting Menu',
                              description='Loading...',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        await m.edit(embed=embed)
        await m.clear_reactions()

        for e in self.EMOJIS.values():
            await m.add_reaction(e)

        page = 0

        while True:
            embed = discord.Embed(title='Crafting Menu',
                                  description='React to craft a flag\nReact :arrow_left: to go backwards a page\nReact :arrow_right: to go forward a page\nReact :eject: to quit',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)

            embed.add_field(name=f'Available flags ({page * 10 + 1}-{min(page * 10 + 10, len(userflags))}/{len(userflags)})',
                            value="\n".join(f'{self.EMOJIS[str(i)]} {userflags[page*10 + i][2]}' for i in range(0, len(userflags[page*10:page*10+10]))))
            await m.edit(embed=embed)

            try:
                r, u = await self.bot.wait_for("reaction_add", check=check, timeout=60)
            except asyncio.TimeoutError:
                return await m.delete()
            await m.remove_reaction(r, u)

            if r.emoji == self.EMOJIS["left_arrow"]:
                page -= 1
                page %= ((len(userflags) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS["right_arrow"]:
                page += 1
                page %= ((len(userflags) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS["eject"]:
                return await m.delete()
            elif r.emoji in self.EMOJIS.values():
                if page*10 + int(r.emoji[0]) < len(userflags):
                    await m.delete()
                    return await self.givecutout(ctx, type, userflags[page*10 + int(r.emoji[0])])

    async def giveflag(self, ctx, userstripes, flaginfo):
        for stripe in userstripes:
            await Inventory.removeitem(self, ctx.author.id, ctx.guild.id, stripe[0], 2)
        await Inventory.additem(self, ctx.author.id, ctx.guild.id, flaginfo[2], flaginfo[0], 1)
        await Leaderboard.addpoints(self, ctx.author.id, ctx.guild.id, 1, 100)

        craftstring = 'a'
        if flaginfo[1][:1] in ['a', 'e', 'i', 'o', 'u']:
            craftstring += 'n'
        embed = discord.Embed(title=f'You crafted {craftstring} {flaginfo[1]}!',
                              description="You've earned 100 points!")
        embed.set_image(url=flaginfo[3])

        await ctx.send(embed=embed)

    async def givecutout(self, ctx, cutoutType, flaginfo):
        print(cutoutType)
        cutoutinfo = await self.executesql(f"SELECT image_id FROM images WHERE text LIKE '{cutoutType}%'", ())
        await Inventory.removeitem(self, ctx.author.id, ctx.guild.id, cutoutinfo[0][0], 1)
        await Inventory.removeitem(self, ctx.author.id, ctx.guild.id, flaginfo[0], 1)

        newcutout = await self.executesql("SELECT image_id, text, url FROM images WHERE text = ?", (f'{flaginfo[2][:-5]} {cutoutType}',))
        await Inventory.additem(self, ctx.author.id, ctx.guild.id, 1, newcutout[0][0], 1)
        await Leaderboard.addpoints(self, ctx.author.id, ctx.guild.id, 1, 150)

        craftstring = 'a'
        if flaginfo[2][:1] in ['a', 'e', 'i', 'o', 'u']:
            craftstring += 'n'
        embed = discord.Embed(title=f'You crafted {craftstring} {newcutout[0][1]}!',
                              description="You've earned 150 points!")
        embed.set_image(url=newcutout[0][2])

        await ctx.send(embed=embed)

    @commands.command(name='craftinghelp', hidden=True)
    async def crafthelp(self, ctx, m=None):
        embed = discord.Embed(title='Crafting help',
                              description='Use `.craft` to open the crafting menu, or add a modifier to go to the menu you would like',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        embed.add_field(name='Flags',
                        value='Collect a pair of each colour from the LGBTQIAP+ flag to craft a flag\nUse `.craft flag` to access the menu immediately',
                        inline=False)
        embed.add_field(name='Cutouts',
                        value='Collect a cutout and combine with a flag to create a flag cutout\nUse `.craft cutout` to access the menu immediately',
                        inline=False)
        embed.add_field(name='Help',
                        value='View help for crafting (this screen)\nUse `.craft help` to access the menu immediately',
                        inline=False)
        if m is not None:
            await m.edit(embed=embed)
        else:
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Crafting(bot))