# -------  Matthew Hammond, 2021  ------
# ----  Plant Bot Premium Commands  ----
# ---------------  v2.1  ---------------


import discord
from discord.ext import commands
import asyncio

from sqlite3 import connect
from datetime import datetime


class Premium(commands.Cog):

    version = "2.1"

    conn = connect("database.db")
    cursor = conn.cursor()

    def __init__(self, bot):

        self.bot = bot

        self.executeSQL("PRAGMA foreign_keys = ON")

        self.executeSQL("""
            CREATE TABLE IF NOT EXISTS premium_users (
                premium_user_id INTEGER PRIMARY KEY,
                user_id INTEGER,
                server_id INTEGER
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
        name = "enablePremium",
        aliases = ["ep"],
        hidden = True,
    )
    @commands.check(premiumCheck)
    async def premiumEnable(self, ctx, id = None):

        try:
            id = int(id)
            user = await self.bot.fetch_user(id)
        except (TypeError, ValueError, discord.errors.NotFound):
            user = None

        if (user):
            if (len(self.executeSQL("""
                SELECT user_id FROM premium_users
                WHERE user_id = ?
            """, (id,)))):
                embed = discord.Embed(
                    title = "Enable Premium",
                    description = "{} already has premium.".format(user.mention),
                    colour = ctx.guild.get_member(self.bot.user.id).colour,
                    timestamp = datetime.now(),
                )
                await ctx.send(embed = embed)

            else:
                self.executeSQL("""
                    INSERT INTO premium_users (user_id)
                    VALUES (?)
                """, (id,))

                embed = discord.Embed(
                    title = "Enable Premium",
                    description = "Premium enabled for {}!".format(user.mention),
                    colour = ctx.guild.get_member(self.bot.user.id).colour,
                    timestamp = datetime.now(),
                )
                await ctx.send(embed = embed)

        else:
            embed = discord.Embed(
                title = "Enable Premium Error",
                description = "Invalid User ID: {}".format(id),
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            await ctx.send(embed = embed)

    @commands.command(
        name = "disablePremium",
        aliases = ["dp"],
        hidden = True,
    )
    @commands.check(premiumCheck)
    async def premiumDisable(self, ctx, id = None):

        try:
            id = int(id)
            user = await self.bot.fetch_user(id)
        except (TypeError, ValueError, discord.errors.NotFound):
            user = None
            
        if (user):
            if (len(self.executeSQL("""
                SELECT user_id FROM premium_users
                WHERE user_id = ?
            """, (id,)))):
                self.executeSQL("""
                    DELETE FROM premium_users
                    WHERE user_id = ?
                """, (id,))

                embed = discord.Embed(
                    title = "Disable Premium",
                    description = "Premium disabled for {}.".format(user.mention),
                    colour = ctx.guild.get_member(self.bot.user.id).colour,
                    timestamp = datetime.now(),
                )
                await ctx.send(embed = embed)

            else:
                embed = discord.Embed(
                    title = "Disable Premium",
                    description = "{} doesn't have premium.".format(user.mention),
                    colour = ctx.guild.get_member(self.bot.user.id).colour,
                    timestamp = datetime.now(),
                )
                await ctx.send(embed = embed)

        else:
            embed = discord.Embed(
                title = "Disable Premium Error",
                description = "Invalid User ID: {}".format(id),
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
            name = "Server Key",
            value = "Give a server of your choice premium using .givePremium!",
        )
        embed.add_field(
            name = "Quizzes",
            value = "Unlimited quizzes/questions/answers!\nCustom emojis!",
        )
        embed.add_field(
            name = "Profiles",
            value = "More fields and a custom colour!",
        )

        await ctx.send(embed = embed)
    
    @commands.command(
        name = "givePremium",
        aliases = ["gp"],
    )
    async def givePremium(self, ctx, id = None):

        premiumId = self.executeSQL("""
            SELECT premium_user_id FROM premium_users
            WHERE user_id = ?
        """, (ctx.author.id,))

        if (len(premiumId)):
            try:
                id = int(id)
                server = await self.bot.fetch_guild(id)
            except (TypeError, ValueError, discord.errors.NotFound):
                server = None
            except discord.errors.Forbidden:
                embed = discord.Embed(
                    title = "Give Premium Error",
                    description = "I am not in that server.".format(id),
                    colour = ctx.guild.get_member(self.bot.user.id).colour,
                    timestamp = datetime.now(),
                )
                await ctx.send(embed = embed)
                return

            if (server):
                self.executeSQL("""
                    UPDATE premium_users
                    SET server_id = ?
                    WHERE user_id = ?
                """, (id, ctx.author.id))

                embed = discord.Embed(
                    title = "Give Premium",
                    description = "You gave {} premium!".format(server.name),
                    colour = ctx.guild.get_member(self.bot.user.id).colour,
                    timestamp = datetime.now(),
                )
                await ctx.send(embed = embed)

            else:
                embed = discord.Embed(
                    title = "Give Premium Error",
                    description = "Invalid Server ID: {}".format(id),
                    colour = ctx.guild.get_member(self.bot.user.id).colour,
                    timestamp = datetime.now(),
                )
                await ctx.send(embed = embed)

        else:
            embed = discord.Embed(
                title = "Give Premium Error",
                description = "You do not have premium.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            await ctx.send(embed = embed)

def setup(bot):
    bot.add_cog(Premium(bot))