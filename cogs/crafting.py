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

    @commands.command(name='craft', help='craft new items')
    async def craft(self, ctx, type):
        def check(r, u):
            return u == ctx.author and r.message == m

        if type.lower() not in ['flag']:
            return

        flags = await self.executesql("SELECT image_id, text, event_id, url FROM images WHERE text LIKE '%flag'", ())
        page = 0
        userstripes = await self.executesql("SELECT i.image_id, inv.count FROM inventories inv INNER JOIN images i USING (image_id) WHERE (inv.user_id = ? AND inv.server_id = ? AND i.text LIKE '%stripe')", (ctx.author.id, ctx.guild.id))

        temp = 22
        for stripe in userstripes:
            if stripe[1] >= 2:
                temp -= 2

        if len(temp):
            return await ctx.send(f"You don't have enough stripes to craft a flag, please try again when you have a flag's worth\nRemaining stripes: {22 - temp}")

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
                    await m.delete()
                    await self.craftflag(ctx, userstripes, flags[page*10 + int(r.emoji[0])])

    async def craftflag(self, ctx, userstripes, flaginfo):
        for stripe in userstripes:
            await Inventory.removeitem(self, ctx.author.id, ctx.guild.id, stripe[0], 1)
        await Inventory.additem(self, ctx.author.id, ctx.guild.id, flaginfo[2], flaginfo[0], 1)
        await Leaderboard.addpoints(self, ctx.author.id, ctx.guild.id, 1, 100)

        craftstring = 'a'
        if flaginfo[1][:1] in ['a', 'e', 'i', 'o', 'u']:
            craftstring += 'n'
        embed = discord.Embed(title=f'You crafted {craftstring} {flaginfo[1]}!',
                              description="You've earned 100 points!")
        embed.set_image(url=flaginfo[3])

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Crafting(bot))