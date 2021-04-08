# -------  Matthew Hammond, 2021  ------
# ----  Plant Bot Premium Commands  ----
# ---------------  v1.0  ---------------


import discord
from discord.ext import commands
import asyncio

from sqlite3 import connect
from datetime import datetime

class Premium(commands.Cog):

    conn = connect("database.db")
    cursor = conn.cursor()

    def __init__(self, bot):

        self.bot = bot

        self.executeSQL("PRAGMA foreign_keys = ON")

        self.executeSQL("""
            CREATE TABLE IF NOT EXISTS premiumServers (
                id INTEGER PRIMARY KEY
            )
        """)

    def executeSQL(self, statement, data = ()):

        self.cursor.execute(statement, data)
        self.conn.commit()
        rows = self.cursor.fetchall()

        return rows

    async def premiumCheck(ctx):
        return 817801520074063974 in [role.id for role in ctx.author.roles]
        # Must have the Plant Team role to edit premium servers.

    @commands.command(
        name = "premium",
        aliases = ["p"],

        brief = "All about premium",
        help = "Use this command to see all the perks you get for buying premium!",

        usage = "[h]"
    )
    async def premium(self, ctx, *args):
        
        if (len(args) and args[0] in ["e", "enable"] and self.premiumCheck(ctx)):
            await self.premiumEnable(ctx, args[1:])

        elif (len(args) and args[0] in ["d", "disable"] and self.premiumCheck(ctx)):
            await self.premiumDisable(ctx, args[1:])

        else:
            await self.premiumHelp(ctx)

    @commands.command(
        name = "enable",
        aliases = ["ep"],
        hidden = True,
    )
    @commands.check(premiumCheck)
    async def premiumEnable(self, ctx, id):

        try:
            id = int(id)
        except ValueError:
            pass

        server = self.bot.get_guild(id)
        if (server):
            if (len(self.executeSQL("""
                SELECT id FROM premiumServers
                WHERE id = ?
            """, (id,)))):
                embed = discord.Embed(
                    title = "Enable Premium",
                    description = "{} already has premium.".format(server.name),
                    colour = ctx.guild.get_member(self.bot.user.id).colour,
                    timestamp = datetime.now(),
                )
                await ctx.send(embed = embed)

            else:
                self.executeSQL("""
                    INSERT INTO premiumServers (id)
                    VALUES (?)
                """, (id,))

                embed = discord.Embed(
                    title = "Enable Premium",
                    description = "Premium enabled for {}!".format(server.name),
                    colour = ctx.guild.get_member(self.bot.user.id).colour,
                    timestamp = datetime.now(),
                )
                await ctx.send(embed = embed)

        else:
            embed = discord.Embed(
                title = "Enable Premium",
                description = "That server does not exist.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            await ctx.send(embed = embed)

    @commands.command(
        name = "disable",
        aliases = ["dp"],
        hidden = True,
    )
    @commands.check(premiumCheck)
    async def premiumDisable(self, ctx, id):

        try:
            id = int(id)
        except ValueError:
            pass

        server = self.bot.get_guild(id)
        if (server):
            if (len(self.executeSQL("""
                SELECT id FROM premiumServers
                WHERE id = ?
            """, (id,)))):
                self.executeSQL("""
                    DELETE FROM premiumServers
                    WHERE id = ?
                """, (id,))

                embed = discord.Embed(
                    title = "Disable Premium",
                    description = "Premium disabled for {}.".format(server.name),
                    colour = ctx.guild.get_member(self.bot.user.id).colour,
                    timestamp = datetime.now(),
                )
                await ctx.send(embed = embed)

            else:
                embed = discord.Embed(
                    title = "Disable Premium",
                    description = "{} doesn't have premium.".format(server.name),
                    colour = ctx.guild.get_member(self.bot.user.id).colour,
                    timestamp = datetime.now(),
                )
                await ctx.send(embed = embed)

        else:
            embed = discord.Embed(
                title = "Disable Premium",
                description = "That server does not exist.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            await ctx.send(embed = embed)

    @commands.command(
        name = "premiumHelp",
        hidden = True,
    )
    async def premiumHelp(self, ctx):

        embed = discord.Embed(
            title = "The Perks of Premium",
            description = "Premium costs XXX.",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        embed.add_field(
            name = "Quizzes",
            value = "Unlimited quizzes/questions/answers!\nCustom emojis!",
        )

        await ctx.send(embed = embed)