#checkers.py

import discord
from discord.ext import commands

def is_guild_owner():
    def predicate(ctx):
        return ctx.message.author == ctx.guild.owner or ctx.message.author.id == 115560604047114248 or ctx.message.author.id == 579785620612972581
    return commands.check(predicate)

def is_plant_owner():
    def predicate(ctx):
        return ctx.message.author.id == 115560604047114248 or ctx.message.author.id == 579785620612972581
    return commands.check(predicate)