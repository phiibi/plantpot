#Halloween.py

import asyncio
import discord
import math
import random
import time

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

    TRICKS = {
        1: 0.5,
        2: 0.2,
        3: 0.15,
        4: 0.1,
        5: 0.05
    }

    TREATS = {
        1: 0.25,
        2: 0.25,
        3: 0.25,
        4: 0.1,
        5: 0.07,
        6: 0.05,
        7: 0.02,
        8: 0.01
    }

    # REWARD STRUCTURE
    # 1 DOUBLE CD
    # 2 RUDE MESSAGE
    # 3 PROFILE PRANK
    # 4 DOUBLE POINTS
    # 5 DM IF MYTHIC/LEGENDARY

    def __init__(self, bot):

        self.bot = bot

        self.setup.start()

    @tasks.loop(count=1)
    async def setup(self):
        await self.executesql("PRAGMA foreign_keys = ON")

        await self.executesql("""CREATE TABLE IF NOT EXISTS rewards (
                    reward_id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    server_id INTEGER NOT NULL,
                    reward INTEGER NOT NULL,
                    start FLOAT NOT NULL,
                    duration FLOAT NOT NULL)""")

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

    @commands.command(name='trickortreat', help='Create and open a Halloween basket')
    async def trickortreat(self, ctx, mod=None):
        if mod == 'sweets':
            return await self.displaysweets(ctx)
        sweets = await self.checkitems(ctx)
        if not sweets:
            return
        if await self.getsweets(ctx, sweets[0]):
            await Inventory.removeitem(self, ctx.author.id, ctx.guild.id, sweets[1][0][0], 1)

    async def displaysweets(self, ctx):
        usersweets = await self.executesql("SELECT i.image_id, i.text, inv.count FROM inventories inv INNER JOIN images i USING (image_id) WHERE (inv.user_id = ? AND inv.server_id = ? AND inv.count > 0 AND i.text LIKE '%Sweet')", (ctx.author.id, ctx.guild.id))
        sweetstring = ''
        totalsweets = 0
        for sweet in usersweets:
            sweetstring += f"**{sweet[1]}**: {sweet[2]}\n"
            totalsweets += sweet[2]

        sweetstring += f'**Total sweets**: {totalsweets}'

        embed = discord.Embed(title='Trick or Treat Sweets',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        embed.add_field(name='Available Sweets', value=sweetstring)

        await ctx.send(embed=embed)

    async def checkitems(self, ctx):
        usersweets = await self.executesql("SELECT i.image_id, i.text, inv.count FROM inventories inv INNER JOIN images i USING (image_id) WHERE (inv.user_id = ? AND inv.server_id = ? AND inv.count > 0 AND i.text LIKE '%Sweet')", (ctx.author.id, ctx.guild.id))
        if len(usersweets) < 7:
            await ctx.send(f"Uh oh, you don't have enough sweets! Please collect {7 - len(usersweets)} more before trying to trick or treat\nUse `.trickortreat sweets` to see how many sweets you have!")
            return False
        userbaskets = await self.executesql("SELECT i.image_id, inv.count FROM inventories inv INNER JOIN images i USING (image_id) WHERE (inv.user_id = ? AND inv.server_id = ? AND inv.count > 0 AND i.text LIKE '%Basket')", (ctx.author.id, ctx.guild.id))
        if not len(userbaskets):
            await ctx.send("Uh oh, you don't have a basket to carry all those sweets in! Please collect a basket before trying to trick or treat!")
            return False
        return [usersweets, userbaskets]

    # Gets given a user input, how many sweets to put into basket
    async def getsweets(self, ctx, sweets):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        sweetstring = ''
        totalsweets = 0
        for sweet in sweets:
            sweetstring += f"**{sweet[1]}**: {sweet[2]}\n"
            totalsweets += sweet[2]

        sweetstring += f'**Total sweets**: {totalsweets}'

        embed = discord.Embed(title="Trick or Treat Menu",
                              description="How many sweets would you like to add to your basket?\nThe more you put in, the more likely you are to get a reward!\nPlease note that you must put at least 7 sweets in!",
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        embed.add_field(name='Available Sweets',
                        value=sweetstring)
        m = await ctx.send(embed=embed)

        while True:
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=60)
            except asyncio.TimeoutError:
                await m.delete()
                return False
            await msg.delete()

            try:
                numsweets = int(msg.content)
                if numsweets > totalsweets:
                    await ctx.send(f"Uh oh, you don't have that many sweets, you only have {totalsweets}. Please enter a lower number.")
                else:
                    await self.balancesweets(ctx, sweets, numsweets)
                    treat = self.calctrickortreat(numsweets)
                    reward = self.calcreward(treat, numsweets)
                    if treat:
                        await self.executetreat(ctx, reward, numsweets)
                    else:
                        await self.executetrick(ctx, reward, numsweets)
                    await m.delete()
                    return True
            except ValueError:
                await ctx.send("Uh oh, I couldn't understand that, please enter a number for me!")

    async def executetrick(self, ctx, reward, numsweets):
        rewardstr = 'A trick for you, '
        if reward == 1:
            rewardstr += "you've been cursed! I've doubled your cooldowns for the next 24 hours"
            await self.addreward(ctx, 1)
        elif reward == 2:
            rewardstr += "you've been haunted! Hope I don't cause too much of a fright..."
            await self.addreward(ctx, 2)
        elif reward == 3:
            points = numsweets * 20
            userpoints = await self.executesql('SELECT score FROM leaderboards WHERE server_id = ? AND user_id = ? AND event_id = ?', (ctx.guild.id, ctx.author.id, 2))
            if points > userpoints[0][0]:
                points = userpoints[0][0]
            await Leaderboard.addpoints(self, ctx.author.id, ctx.guild.id, 2, -points)
            rewardstr += f"I'm taking 20 points for every sweet in your basket, that's {points} points!"
        elif reward == 4:
            rewardstr += f"you've been pranked! Your profile is defaced for the next 24 hours"
            await self.addreward(ctx, 3)
        elif reward == 5:
            points = numsweets * 40
            userpoints = await self.executesql('SELECT score FROM leaderboards WHERE server_id = ? AND user_id = ? AND event_id = ?', (ctx.guild.id, ctx.author.id, 2))
            if points > userpoints[0][0]:
                points = userpoints[0][0]
            await Leaderboard.addpoints(self, ctx.author.id, ctx.guild.id, 2, -points)
            rewardstr += f"I'm taking 40 points for every sweet in your basket, that's {points} points!"

        await ctx.send(rewardstr)

    async def executetreat(self, ctx, reward, numsweets):
        rewardstr = 'A treat for you, '
        if reward == 1:
            await Leaderboard.addpoints(self, ctx.author.id, ctx.guild.id, 2, 50)
            rewardstr += "I'll give you 50 points!"
        elif reward == 2:
            rewardstr += "I've started a frenzy! You get double points on pickup for the next 30 minutes"
            await self.addreward(ctx, 4, 1800)
        elif reward == 3:
            rewardstr += "I've given you the eye of the beholder! For the next 24 hours, I'll DM you if I post a mythic or legendary"
            await self.addreward(ctx, 5)
        elif reward == 4:
            await Leaderboard.addpoints(self, ctx.author.id, ctx.guild.id, 2, 50)
            rewardstr += "I'll give you 100 points!"
        elif reward == 5:
            mythics = await self.executesql("SELECT image_id, text FROM images WHERE event_id = ? AND rarity_id = ?", (2, 7))
            m = random.choice(mythics)
            await Inventory.additem(self, ctx.author.id, ctx.guild.id, 2, m[0], 1)
            await Leaderboard.addpoints(self, ctx.author.id, ctx.guild.id, 2, 200)
            rewardstr += f"I'll give you the mythic item {m[1]} and 200 points!"
        elif reward == 6:
            await Leaderboard.addpoint(self, ctx.author.id, ctx.guild.id, "me!!", 0)
            await Leaderboard.addpoints(self, ctx.author.id, ctx.guild.id, 2, 250)
            rewardstr += f"I'll give you myself and 250 points! Please check your spring inventory for me!!"
        elif reward == 7:
            legendaries = await self.executesql("SELECT image_id, text FROM images WHERE event_id = ? AND rarity_id = ?", (2, 2))
            l = random.choice(legendaries)
            await Inventory.additem(self, ctx.author.id, ctx.guild.id, 2, l[0], 1)
            await Leaderboard.addpoints(self, ctx.author.id, ctx.guild.id, 2, 300)
            rewardstr += f"I'll give you the legendary item {l[1]} and 300 points!"
        elif reward == 8:
            points = numsweets * 50
            await Leaderboard.addpoints(self, ctx.author.id, ctx.guild.id, 2, numsweets)
            rewardstr += f"I'll give 50 points for every sweet in your basket, that's {points} points!"

        await ctx.send(rewardstr)

    async def addreward(self, ctx, reward, duration=86400):
        before = await self.executesql("SELECT reward_id, start, duration FROM rewards WHERE user_id = ? AND server_id = ? AND reward = ?",
                                       (ctx.author.id, ctx.guild.id, reward))
        if len(before):
            if (before[0][1] + before[0][2]) > time.time():
                await self.executesql('UPDATE rewards SET duration = ? WHERE reward_id = ?', (before[0][2] + duration, before[0][0]))
            else:
                await self.executesql('UPDATE rewards SET duration = ?, start = ? WHERE reward_id = ?', (duration, time.time(), before[0][0]))
        else:
            await self.executesql('INSERT INTO rewards (user_id, server_id, reward, start, duration) VALUES (?, ?, ?, ?, ?)',
                                  (ctx.author.id, ctx.guild.id, reward, time.time(), duration))
    # Calculates a reward
    def calcreward(self, treat, numsweets):
        odds = random.random()
        if treat:
            reward = self.processtreats(numsweets).items()
        else:
            reward = self.TRICKS.items()
        for kv in reward:
            odds -= kv[1]
            if odds < 0:
                return kv[0]

    def processtreats(self, numsweets):
        multiplier = (2 / (1 + 5.8 * math.exp(-0.25 * numsweets)))
        dist = (0.25 / multiplier) * 3
        return {
            1: 0.25 / multiplier,
            2: 0.25 / multiplier,
            3: 0.25 / multiplier,
            4: 0.1 + (dist / 5),
            5: 0.07 + (dist / 5),
            6: 0.05 + (dist / 5),
            7: 0.02 + (dist / 5),
            8: 0.01 + (dist / 5)
        }
    # Calculates whether to trick or treat
    def calctrickortreat(self, sweets):
        multiplier = 2 / (1 + 5.8 * math.exp(-0.25 * sweets))
        return random.random() > (0.45 / multiplier)

    # Returns a list of sweets to be removed
    async def balancesweets(self, ctx, sweets, count):
        newsweets = []
        for sweet in sweets:
            newsweets.append([sweet[0], sweet[2]])
        removals = {}
        for sweet in newsweets:
            await Inventory.removeitem(self, ctx.author.id, ctx.guild.id, sweet[0], 1)
            sweet[1] -= 1
        for i in range(count - 7):
            newsweets.sort(key=itemgetter(1), reverse=True)
            topsweet = removals.get(newsweets[0][0])
            if topsweet:
                removals.update({newsweets[0][0]: topsweet + 1})
            else:
                removals.update({newsweets[0][0]: 1})
            newsweets[0][1] -= 1
        for sweet in removals.items():
            await Inventory.removeitem(self, ctx.author.id, ctx.guild.id, sweet[0], sweet[1])


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

# 10 / 1 + 300 * math.exp(-sweets)

def setup(bot):
    bot.add_cog(Halloween(bot))
