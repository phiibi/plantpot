#crafting.py

import asyncio
import discord

from discord.ext import commands, tasks
from aiosqlite import connect
from cogs.pinventory import PrideInventory

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

    def __init__(self, bot):

        self.bot = bot

        self.setup.start()

    @tasks.loop(count=1)
    async def setup(self):
        await self.executesql("PRAGMA foreign_keys = ON")
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

    @commands.command(name='craft', help='craft new items')
    async def craft(self, ctx, type):
        def check(r, u):
            return u == ctx.author and r.message == m

        if type.lower() not in ['flags']:
            return

        flags = await self.executesql("SELECT image_id, text, event_id FROM images WHERE text LIKE '%flag'", ())
        page = 0
        userstripes = await self.executesql("SELECT inv.unique_item_id, inv.image_id FROM inventories inv INNER JOIN images i USING(image_id) WHERE inv.user_id = ? AND inv.server_id = ? AND (i.name LIKE '%stripe')", (ctx.author.id, ctx.guild.id))

        if len(userstripes) > 11:
            return await ctx.send(f"You don't have enough stripes to craft a flag, please try again when you have a flag's worth\nRemaining stripes: {11-len(userstripes)}")

        embed = discord.Embed(title='Crafting Menu',
                              description='Loading...',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        m = await ctx.send(embed=embed)

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
                return
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
                    await self.craftflag(ctx, userstripes, flags[page*10 + int(r.emoji[0])][0], flags[page*10 + int(r.emoji[0])][2])

    async def craftflag(self, ctx, userstripes, flagid, eventid):
        for stripe in userstripes:
            await PrideInventory.removeitem(self, ctx.author.id, ctx.guild.id, stripe[1], 1)
        await PrideInventory.additem(self, ctx.author.id, ctx.guild.id, eventid, flagid, 1)

def setup(bot):
    bot.add_cog(Crafting(bot))