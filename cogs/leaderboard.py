#leaderboard.py

import json
import operator
import discord

from discord.ext import commands


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(help='leaderboard related commands, ".leaderboard help" for more help')
    async def leaderboard(self, ctx):
        if ctx.invoked_subcommand is None:
            await Leaderboard.getlb(self, ctx)
            return

    @leaderboard.command(name='help', help='full help for leaderboard commands')
    async def help(self, ctx, command):
        commandhelp = {"leaderboard": "`.leaderboard` or `.top10` will give you the list of the top 10 users this event!",
                       "myleaderboard": "`.myleaderboard [user]` will give you your current points and position this event, mentioning [user] will show your their position"}
        helpstr = commandhelp.get(command)
        if helpstr is None:
            await ctx.send('please enter a valid command, type ```.leaderboard help``` for a command list')
        else:
            embed = discord.Embed()
            embed.title = f'{command} help'
            embed.description = helpstr
            await ctx.send(embed=embed)

    @commands.command(name='myleaderboard', help='shows yours, or a given user\'s position on leaderboard', hidden=True)
    async def position(self, ctx, *, username: discord.Member=None):
        sid = ctx.guild.id
        with open(f'cogs/leaderboards/lb{sid}.json', 'r') as file:
            d = json.loads(file.read())
        if username is None:
            if await Leaderboard.checkuser(self, ctx.message.author.id, d):
                lb = d['users']
                lb.sort(key=operator.itemgetter('points'), reverse=True)
                for i in range(len(lb)):
                    if lb[i]['userid'] == ctx.message.author.id:
                        embed = discord.Embed()
                        embed.title = f'you are in #{i+1} place!'
                        embed.description = 'you have collected {0} items so far! keep it up!'.format(lb[i]['points'])
                        embed.set_thumbnail(url=ctx.message.author.avatar_url_as())
                        return await ctx.send(embed=embed)
            await ctx.send('you haven\'t collected anything this event!')
        else:
            if await Leaderboard.checkuser(self, username.id, d):
                lb = d['users']
                lb.sort(key=operator.itemgetter('points'), reverse=True)
                for i in range(len(lb)):
                    if lb[i]['userid'] == username.id:
                        embed = discord.Embed()
                        embed.title = f'{username.display_name} is #{i+1} place!'
                        embed.description = 'they have collected {0} items so far!'.format(lb[i]['points'])
                        embed.set_thumbnail(url=username.avatar_url_as())
                        return await ctx.send(embed=embed)
            await ctx.send(f'{username.display_name} has\'t collected anything this event!')


    @commands.command(name='top10', help='displays the current leaderboard', hidden=True)
    async def getlb(self, ctx):
        sid = ctx.guild.id
        with open(f'cogs/leaderboards/lb{sid}.json', 'r') as file:
            d = json.loads(file.read())
        lb = d['users']
        lb.sort(key=operator.itemgetter('points'), reverse=True)
        lbtxt = ''
        if len(lb) < 10:
            x = len(lb)
        else:
            x = 10

        for i in range(x):
            uid = await self.bot.fetch_user(lb[i]['userid'])
            lbtxt += '{0}. **{1}** - {2}\n'.format(i+1, uid.display_name, lb[i]['points'])
        embed = discord.Embed()
        embed.title = f'The top {x} users'
        embed.description = lbtxt
        await ctx.send(embed=embed)


    async def addpoint(self, uid, sid, image, points):
        with open(f'cogs/leaderboards/lb{sid}.json', 'r') as file:
            d = json.loads(file.read())
        temp = d
        updated = await Leaderboard.adduser(self, uid, image, d, points)
        if updated is None:
            for i, user in enumerate(d['users']):
                if user['userid'] == uid:
                    images = user['images']
                    images.append(image)
                    temp['users'][i].update({"userid": uid,
                                             "points": user['points'] + points,
                                             "images": images})
                    break
        else:
            temp = updated
        with open(f'cogs/leaderboards/lb{sid}.json', 'w') as file:
            json.dump(temp, file)


    async def adduser(self, uid, image, data, points):
        c = await Leaderboard.checkuser(self, uid, data)
        if c:
            return None
        else:
            data['users'].append({"userid": uid,
                                  "points": points,
                                  "images": [image]})
            return data

    async def checkuser(self, userid, data):
        for user in data['users']:
            if user['userid'] == userid:
                return True
        return False

    def checkimage(self, uid, sid, image):
        with open(f'cogs/leaderboards/lb{sid}.json', 'r') as file:
            d = json.loads(file.read())
        for user in d['users']:
            if user['userid'] == uid and user['images'].count(image) >= 1:
                return True
        return False

    @leaderboard.command(name='clear', help='clears the leaderboard', hidden=True)
    @commands.is_owner()
    async def clearlb(self, ctx):
        cleared = {"users": []}
        with open(f'cogs/leaderboards/lb{ctx.guild.id}.json', 'w') as file:
            json.dump(cleared, file)

    # ------------- Error handling ------------- #

    @help.error
    async def helperror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            embed = discord.Embed()
            embed.title = 'please format this command as .leaderboard help [command]'
            embed.description = """leaderboard commands are:
            **leaderboard**: lists the top 10 users this event
            **myleaderboard**: displays your position and points this event"""
            await ctx.send(embed=embed)

class AnimeLeaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(help='anime leaderboard related commands')
    async def ani(self, ctx):
        if ctx.invoked_subcommand is None:
            await AnimeLeaderboard.getlb(self, ctx)
            return

    @commands.command(name='animetop10', help='displays the current anime leaderboard', aliases=['animeleaderboard'])
    async def getlb(self, ctx):
        sid = ctx.guild.id
        with open(f'cogs/leaderboards/a{sid}.json', 'r') as file:
            d = json.loads(file.read())
        lb = d['users']
        lb.sort(key=operator.itemgetter('points'), reverse=True)
        lbtxt = ''
        if len(lb) < 10:
            x = len(lb)
        else:
            x = 10

        for i in range(x):
            uid = await self.bot.fetch_user(lb[i]['userid'])
            lbtxt += '{0}. **{1}** - {2}\n'.format(i+1, uid.display_name, lb[i]['points'])
        embed = discord.Embed()
        embed.title = f'The top {x} users'
        embed.description = lbtxt
        await ctx.send(embed=embed)

    @commands.command(name='myanimeleaderboard', help='shows yours, or a given user\'s position on the anime leaderboard')
    async def position(self, ctx, *, username: discord.Member=None):
        sid = ctx.guild.id
        with open(f'cogs/leaderboards/a{sid}.json', 'r') as file:
            d = json.loads(file.read())
        if username is None:
            if await Leaderboard.checkuser(self, ctx.message.author.id, d):
                lb = d['users']
                lb.sort(key=operator.itemgetter('points'), reverse=True)
                for i in range(len(lb)):
                    if lb[i]['userid'] == ctx.message.author.id:
                        embed = discord.Embed()
                        embed.title = f'you are in #{i+1} place!'
                        embed.description = 'you have collected {0} items so far! keep it up!'.format(lb[i]['points'])
                        embed.set_thumbnail(url=ctx.message.author.avatar_url_as())
                        return await ctx.send(embed=embed)
            await ctx.send('you haven\'t collected anything this event!')
        else:
            if await Leaderboard.checkuser(self, username.id, d):
                lb = d['users']
                lb.sort(key=operator.itemgetter('points'), reverse=True)
                for i in range(len(lb)):
                    if lb[i]['userid'] == username.id:
                        embed = discord.Embed()
                        embed.title = f'{username.display_name} is #{i+1} place!'
                        embed.description = 'they have collected {0} items so far!'.format(lb[i]['points'])
                        embed.set_thumbnail(url=username.avatar_url_as())
                        return await ctx.send(embed=embed)
            await ctx.send(f'{username.display_name} has\'t collected anything this event!')

    async def addpoint(self, uid, sid, imageurl, imagename, points):
        with open(f'cogs/leaderboards/a{sid}.json', 'r') as file:
            d = json.loads(file.read())
        temp = d
        updated = await AnimeLeaderboard.adduser(self, uid, imageurl, imagename, points,  d)
        if updated is None:
            for i, user in enumerate(d['users']):
                if user['userid'] == uid:
                    image_u = user['image_url']
                    image_u.append(imageurl)
                    image_n = user['image_name']
                    image_n.append(imagename)
                    temp['users'][i].update({"userid": uid,
                                             "points": user['points'] + points,
                                             "image_name": image_n,
                                             "image_url": image_u})
                    break
        else:
            temp = updated
        with open(f'cogs/leaderboards/a{sid}.json', 'w') as file:
            json.dump(temp, file)

    async def adduser(self, uid, imageurl, imagename, points, data):
        if await Leaderboard.checkuser(self, uid, data):
            print('user found')
            return None
        else:
            data['users'].append({"userid": uid,
                                  "points": points,
                                  "image_name": [imagename],
                                  "image_url": [imageurl]})
            return data

    def checkimage(self, uid, sid, name):
        with open(f'cogs/leaderboards/a{sid}.json', 'r') as file:
            d = json.loads(file.read())
        for user in d['users']:
            if user['userid'] == uid and user['image_name'].count(name) >= 1:
                return True
        return False

    @ani.command(name='clear', help='clears the leaderboard', hidden=True)
    @commands.is_owner()
    async def clearlb(self, ctx):
        cleared = {"users": []}
        with open(f'cogs/leaderboards/a{ctx.guild.id}.json', 'w') as file:
            json.dump(cleared, file)

def setup(bot):
    bot.add_cog(Leaderboard(bot))
    bot.add_cog(AnimeLeaderboard(bot))


