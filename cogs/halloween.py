#Halloween.py

import asyncio
import discord

from aiosqlite import connect
from cogs.inventory import Inventory
from cogs.leaderboard import Leaderboard
from discord.ext import commands, tasks
from operator import itemgetter

class Halloween(commands.Cog):
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

        @commands.command(name='trickortreat', help='create and open a Halloween basket')
        async def trickortreat(self, ctx):
            if not await self.checkItems(ctx):
                return
            ...

        async def checkItems(self, ctx):
            usersweets = await self.executesql("SELECT i.image_id, i.text, inv.count FROM inventories inv INNER JOIN images i USING (image_id) WHERE (inv.user_id = ? AND inv.server_id = ? AND i.text LIKE '%sweet')", (ctx.author.id, ctx.guild.id))
                if len(usersweets) < 7:
                    # TODO add text which tells them which sweets their missing
                    await ctx.send(f"Uh oh, you don't have enough sweets! Please collect {7 - len(usersweets)} more before trying to trick or treat")
                    return False
            userbaskets = await self.executesql("SELECT i.image_id, inv.count FROM inventories inv INNER JOIN images i USING (image_id) WHERE (inv.user_id = ? AND inv.server_id = ? AND i.text LIKE '%basket')", (ctx.author.id, ctx.guild.id))
                if not len(userbaskets):
                    await ctx.send("Uh oh, you don't have a basket to carry all those sweets in! Please collect a basket before trying to trick or treat!")
                    return False
            return [usersweets, userbaskets]

        async def getSweets(self, ctx, sweets):
            def check(r, u):
                return u == ctx.author and r.message == m

            sweetstring = ''
            for sweet in sweets:
                sweetstring += f"**{sweet[1]}**: {sweet[2]}\n"

            embed = discord.Embed(title="Trick or Treat Menu",
                                                   description="How many sweets would you like to add to your basket?\nThe more you put in, the more likely you are to get a reward!\nPlease note that you must put at least 7 sweets in!",
                                                   colour=ctx.guild.get_member(self.bot.user.id).colour)
            embed.add_field(name='Available Sweets',
                                        field=sweetstring)
            m = await ctx.send(embed)

            while True:
                try:
                    msg = await self.bot.wait_for("message", check=check, timeout=60)
                except asyncio.TimeoutError:
                    await m.delete()
                    return False
                await msg.delete()

                try:
                    numsweets = int(msg.content)
                    return self.balanceSweets(sweets, numsweets)
                except ValueError:
                    await ctx.send("Uh oh, I couldn't understand that, please enter a number for me!")

    async def getPoints(self, ctx, m):
        def check(r, u):
            return u == ctx.author and r.message == m

        points = await self.executesql("SELECT lb.points FROM leaderboard lb INNER JOIN events e USING (event_id) WHERE e.name = 'Halloween 2021' AND lb.user_id = ? AND lb.server_id = ?", (ctx.author.id, ctx.guild.id))

        if not len(points):
            await ctx.send("You don't have any points! Please try again once you have some points")
            return False
        elif not points[0][0]:
            await ctx.send("You don't have any points! Please try again once you have some points")
            return False

        embed = discord.Embed(title="Trick or Treat Menu",
                                                description="Please choose how many points to barter on this trick or treat! Don't worry, you won't lose those points, most likely...",
                                                colour=ctx.guild.get_member(self.bot.user.id).colour)

        embed.add_field(name="Available Points",
                                    value=points[0][0])
        await m.edit(embed=embed)
        
        while True:
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=60)
            except asyncio.TimeoutError:
                await m.delete()
                return False
            await msg.delete()

            try:
                numpoints = int(msg.content)
                if numpoints > points[0][0]:
                    await ctx.send(f"Uh oh, you don't have that many points! You have {points[0][0]} points, please enter a number smaller than that")
                elif not numpoints:
                    await ctx.send("You have to barter some points, please enter a number bigger than 0!")
                else:
                    if numpoints < 0:
                        # TODO add guarenteed trick
                        await ctx.send("Please do not enter negative numbers, I have converted your input into a positive number")
                    return abs(numpoints)
            except ValueError:
                await ctx.send("Uh oh, I couldn't understand that, please enter a number for me!")

    def balanceSweets(self, sweets, count):
        removals = {}
        while count:
            sweets.sort(key=itemgetter(2))
            topsweet = removals.get(sweets[0][0])
            if topsweet:
                removals.update({sweets[0][0]}: topsweet + 1)
            else:
                removals.update({sweets[0][0]: 1})
            count -= 1
        return removals

    """@commands.command(name='craftinghelp', hidden=True)
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
            await ctx.send(embed=embed) """

def setup(bot):
    bot.add_cog(Halloween(bot))
