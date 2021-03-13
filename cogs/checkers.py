#checkers.py

import discord
from discord.ext import commands

def is_plant_admin():
    def predicate(ctx):
        r = ctx.message.author.roles
        817801520074063974

        return ctx.message.author.roles == 85309593344815104
    return commands.check(predicate)