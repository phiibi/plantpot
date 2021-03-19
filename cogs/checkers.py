#checkers.py

import discord
import time
from discord.ext import commands

def is_guild_owner():
    def predicate(ctx):
        return ctx.message.author == ctx.guild.owner or ctx.message.author.id == 115560604047114248 or ctx.message.author.id == 579785620612972581
    return commands.check(predicate)

def is_plant_owner():
    def predicate(ctx):
        return ctx.message.author.id == 115560604047114248 or ctx.message.author.id == 579785620612972581
    return commands.check(predicate)

class SpamChecker:
    def __init__(self):
        self.users = {}

    async def adduser(self, ctx, userid):
        self.users.update({userid: time.time()})

    async def checkuser(self, ctx, userid):
        if self.users.get(userid) - time.time() < 150:
            return True
        if self.users.get(userid) - time.time() > 150 or self.users.get(userid) is None:
            self.users.update({userid: time.time()})
            return False

    async def unloadusers(self, ctx):
        for u in self.users:
            if self.users[u] - time.time() > 150:
                del self.users[u]