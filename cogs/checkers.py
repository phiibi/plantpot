#checkers.py

import discord
import time
from discord.ext import commands

def is_guild_owner():
    def predicate(ctx):
        return ctx.message.author.id == ctx.guild.owner_id or ctx.message.author.id == 115560604047114248 or ctx.message.author.id == 579785620612972581
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
        u = self.users.get(userid)
        if u is None or time.time() - u > 150:
            await self.adduser(ctx, userid)
            return False
        else:
            return True

    async def unloadusers(self, ctx):
        for u in self.users:
            if self.users[u] - time.time() > 150:
                del self.users[u]

class blacklistSpam:
    def __init__(self):
        self.users = []

    async def adduser(self, userid):
        await self.unloadtimes(time.time())
        print(self.users)
        if await self.checkuser(userid):
            for user in self.users:
                if user['userid'] == userid:
                    user['times'].append(time.time())
                    if len(user['times']) >= 2:
                        print(self.users)
                        return True
        else:
            self.users.append({"userid": userid, "times": [time.time()]})
            return False

    async def checkuser(self, userid):
        for user in self.users:
            if user['userid'] == userid:
                return True
        return False

    async def unloadtimes(self, time):
        for user in self.users:
            for t in user['times']:
                if (time - t) > 120:
                    user['times'].remove(t)
            if not user['times']:
                del self.users[user]

