#serversettings

import json
import discord

from discord.ext import commands
from cogs import checkers


class ServerSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='server')
    async def server(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    def is_adri():
        def predicate(ctx):
            return ctx.message.author.id == 375274992331390976
        return commands.check(predicate) 
    
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

    @commands.command(name='loading', hidden=True)
    @commands.is_owner()
    async def loading(self, ctx, *, module: str):
        """Loads a module."""
        try:
            await self.bot.load_extension(f'cogs.{module}')
        except Exception as e:
            await ctx.send('{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send('\N{OK HAND SIGN}')

    

def setup(bot):
    bot.add_cog(ServerSettings(bot))

