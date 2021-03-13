#serversettings

import json
import discord

from discord.ext import commands


class ServerSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='manualsetup', hidden=True)
    @commands.is_owner()
    async def manualsetup(self, ctx):
        print(ctx.guild.id)
        ServerSettings.setupserver(self, ctx.guild.id)

    def setupserver(self, serverid):
        with open('cogs/servers.json', 'r') as file:
            d = json.loads(file.read())
        ServerSettings.addserver(self, serverid, d);
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
                                    "cd": 90,
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

