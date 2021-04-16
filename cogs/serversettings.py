#serversettings

import json
import discord

from discord.ext import commands
from cogs import checkers


class ServerSettings(commands.Cog):
    version = '0.1'
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='server', hidden=True)
    async def server(self, ctx):
        if ctx.invoked_subcommand is None:
            pass
    
    @server.command(name='manualsetup', hidden=True)
    @checkers.is_guild_owner()
    async def manualsetup(self, ctx):
        print(ctx.guild.id)
        ServerSettings.setupserver(self, ctx.guild.id)
        await ctx.send('server set up!')

    @server.command(name='setcd', hidden=True)
    @checkers.is_guild_owner()
    async def setcd(self, ctx, t: int):
        with open('cogs/servers.json', 'r') as file:
            d = json.loads(file.read())
        newcd = {"cd": t}
        for i, s in enumerate(d['servers']):
            if s['serverid'] == ctx.guild.id:
                d['servers'][i].update(newcd)
                break
        with open('cogs/servers.json', 'w') as file:
            json.dump(d, file)

    async def getcd(self, ctx):
        with open('cogs/servers.json', 'r') as file:
            d = json.loads(file.read())
        for s in d['servers']:
            if s['serverid'] == ctx.guild.id:
                return s['cd']

    def setupserver(self, serverid):
        with open('cogs/servers.json', 'r') as file:
            d = json.loads(file.read())
        d = ServerSettings.addserver(self, serverid, d);
        if d is None:
            pass
        else:
            with open('cogs/servers.json', 'w') as file:
                json.dump(d, file)

    def addserver(self, serverid, data):
        if ServerSettings.checkserver(self, serverid, data):
            data = None
        else:
            data['servers'].append({"serverid": serverid,
                                    "store": "randomImages",
                                    "wcid": None, #welcome-channel-id
                                    "wm": None, #welcome-message
                                    "lbf": f"lb{serverid}",
                                    "cd": 60,
                                    "anime": None,
                                    "emoji": '\U0001F338'
                                    })
            setupjson = {"users": []}
            with open (f'cogs/leaderboards/lb{serverid}.json', 'a+') as f:
                json.dump(setupjson, f)
            with open (f'cogs/leaderboards/a{serverid}.json', 'a+') as f:
                json.dump(setupjson, f)
        return data

    def checkserver(self, serverid, data):
        for server in data['servers']:
            if server['serverid'] == serverid:
                return True
        return False


class ServerSetter:
    def __init__(self, guild):
        self.sid = guild.id

    async def setupserver(self):
        with open('cogs/servers.json', 'r') as file:
            d = json.loads(file.read())
        d = self.addserver(d)
        if d is None:
            pass
        else:
            with open('cogs/servers.json', 'w') as file:
                json.dump(d, file)

    def addserver(self, data):
        if self.checkserver(data):
            data = None
        else:
            data['servers'].append({"serverid": self.sid,
                                    "store": "randomImages",
                                    "wcid": None, #welcome-channel-id
                                    "wm": None, #welcome-message
                                    "lbf": f"lb{self.sid}",
                                    "cd": 60,
                                    "anime": None,
                                    "emoji": '\U0001F338'
                                    })
            setupjson = {"users": []}
            with open (f'cogs/leaderboards/lb{self.sid}.json', 'a+') as f:
                json.dump(setupjson, f)
            with open (f'cogs/leaderboards/a{self.sid}.json', 'a+') as f:
                json.dump(setupjson, f)
        return data

    def checkserver(self, data):
        for server in data['servers']:
            if server['serverid'] == self.sid:
                return True
        return False

def setup(bot):
    bot.add_cog(ServerSettings(bot))

