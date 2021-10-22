#leaderboard.py

import json
import operator
import discord
import asyncio

from discord.ext import commands, tasks
from cogs import checkers
from aiosqlite import connect

class Leaderboard(commands.Cog):
    version = '0.1'
    EMOJIS = {
        "0":              "0️⃣",
        "1":              "1️⃣",
        "2":              "2️⃣"}
    def __init__(self, bot):
        self.bot = bot

        self.setup.start()

    @tasks.loop(count=1)
    async def setup(self):
        await self.executesql("PRAGMA foreign_keys = ON")

        await self.executesql("""CREATE TABLE IF NOT EXISTS leaderboards (
                        lb_id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        event_id INTEGER NOT NULL,
                        server_id INTEGER NOT NULL,
                        score INTEGER NOT NULL,
                        CONSTRAINT fk_event FOREIGN KEY (event_id) REFERENCES events(event_id))""")

    @setup.before_loop
    async def before_setup(self):
        await self.bot.wait_until_ready()

    #executesql is now asynchronous to prevent blocking
    async def executesql(self, statement, data=()):
        db = await connect('database.db')
        cursor = await db.execute(statement, data)
        await db.commit()
        rows = await cursor.fetchall()
        await cursor.close()
        await db.close()

        #returns a list of Row objects which can be indexed like an array
        return list(rows)

    @commands.group(help='please use .leaderboard help for more help')
    async def leaderboard(self, ctx):
        if ctx.invoked_subcommand is None:
            await Leaderboard.lb(self, ctx)
            return

    @commands.command(name='myleaderboard', help='shows yours, or a given user\'s position on leaderboard', aliases=['mylb', 'position', 'pos', 'mypos'])
    async def mylb(self, ctx, *, username: discord.Member=None):
        return await self.mylbmenu(ctx, username)

    async def mylbmenu(self, ctx, username=None):
        if ctx.guild.id == 813532137050341407:
            desc = 'Please react with a number based on which leaderboard you would like to see your position on\nReact with :zero: for the regular leaderboards\nReact with :one: for the anime leaderboards\nReact with :two: for the pride leaderboards\nReact with :three: for the Halloween leaderboards\nOr wait 60s to cancel'
        else:
            desc = 'Please react with a number based on which leaderboard you would like to see your position on\nReact with :zero: for the regular leaderboards\nReact with :one: for the anime leaderboards\nReact with :two: for the pride leaderboards\nOr wait 60s to cancel'
        embed = discord.Embed(title='Leaderboard Position Menu',
                              description=desc,
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        m = await ctx.send(embed=embed)

        await m.add_reaction(self.EMOJIS["0"])
        await m.add_reaction(self.EMOJIS["1"])
        await m.add_reaction(self.EMOJIS['2'])
        if ctx.guild.id == 813532137050341407:
            await m.add_reaction(self.EMOJIS['3'])

        def check(r, u):
            if r.message == m and u == ctx.author:
                return r, u

        while True:
            try:
                r, u = await self.bot.wait_for('reaction_add', check=check, timeout=60)
                if r.emoji == self.EMOJIS["0"]:
                    await m.clear_reactions()
                    return await self.position(ctx, m=m, username=username)
                elif r.emoji == self.EMOJIS["1"]:
                    await m.clear_reactions()
                    return await AnimeLeaderboard.position(self, ctx, m, username=username)
                elif r.emoji == self.EMOJIS['2']:
                    await m.clear_reactions()
                    p = await self.executesql('SELECT score FROM leaderboards WHERE user_id = ? AND event_id = ? AND server_id = ?', (ctx.author.id, 1, ctx.guild.id))
                    return await self.displayposition(ctx, m, 1, p[0][0])
                elif r.emoji == self.EMOJIS['3']:
                    # TODO refine to one sql statement
                    await m.clear_reactions()
                    p = await self.executesql('SELECT score FROM leaderboard WHERE user_id = ? AND event_id = ? AND server_id = ?', (ctx.author.id, 2, ctx.guild.id))
                    return await self.displayposition(ctx, m, 2, p[0][0])
            except asyncio.TimeoutError:
                return await m.delete()

    async def addpoints(self, userid, serverid, eventid, points):
        userpoints = await self.executesql('SELECT lb_id, score FROM leaderboards WHERE user_id = ? AND server_id = ? AND event_id = ?', (userid, serverid, eventid))

        if len(userpoints):
            await self.executesql('UPDATE leaderboards SET score = ? WHERE lb_id = ?', (userpoints[0][1] + points, userpoints[0][0]))
        else:
            await self.executesql('INSERT INTO leaderboards (user_id, event_id, server_id, score) VALUES (?, ?, ?, ?)', (userid, eventid, serverid, points))

    @commands.command(name='top10', help='displays the current leaderboard', aliases=['lb', 'top'])
    async def lb(self, ctx):
        return await self.lbmenu(ctx)

    async def lbmenu(self, ctx):
        if ctx.guild.id == 813532137050341407:
            desc = 'Please react with a number based on which leaderboard you would like to see your position on\nReact with :zero: for the regular leaderboards\nReact with :one: for the anime leaderboards\nReact with :two: for the pride leaderboards\nReact with :three: for the Halloween leaderboards\nOr wait 60s to cancel'
        else:
            desc = 'Please react with a number based on which leaderboard you would like to see your position on\nReact with :zero: for the regular leaderboards\nReact with :one: for the anime leaderboards\nReact with :two: for the pride leaderboards\nOr wait 60s to cancel'
        embed = discord.Embed(title='Leaderboard Menu',
                              description=desc,
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        m = await ctx.send(embed=embed)

        await m.add_reaction(self.EMOJIS["0"])
        await m.add_reaction(self.EMOJIS["1"])
        await m.add_reaction(self.EMOJIS['2'])
        if ctx.guild.id == 813532137050341407:
            await m.add_reaction(self.EMOJIS['3'])

        def check(r, u):
            if r.message == m and u == ctx.author:
                return r, u

        while True:
            try:
                r, u = await self.bot.wait_for('reaction_add', check=check, timeout=60)
                if r.emoji == self.EMOJIS["0"]:
                    await m.clear_reactions()
                    return await self.getlb(ctx, m)
                elif r.emoji == self.EMOJIS["1"]:
                    await m.clear_reactions()
                    return await AnimeLeaderboard.getlb(self, ctx, m)
                elif r.emoji == self.EMOJIS['2']:
                    await m.clear_reactions()
                    return await self.displayleaderboard(ctx, m, 1, 'pride')
                elif r.emoji == self.EMOJIS['3']:
                    await m.clear_reactions()
                    return await self.displayleaderboard(ctx, m, 2, 'Halloween')

            except asyncio.TimeoutError:
                return await m.delete()

    async def displayleaderboard(self, ctx, m, eventid, eventname):
        await m.clear_reactions()

        users = await self.executesql('SELECT user_id, score FROM leaderboards WHERE event_id = ? AND server_id = ? ORDER BY score DESC LIMIT 10', (eventid, ctx.guild.id))

        embed = discord.Embed(title=f'{eventname} top {len(users)}',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        lbtxt = ''
        for i in range(0, len(users)):
            user = await self.bot.fetch_user(users[i][0])
            lbtxt += f'{i+1}. **{user.display_name}** - {users[i][1]}\n'
        embed.description = lbtxt
        await m.edit(embed=embed)

    async def displayposition(self, ctx, m, eventid, score):
        await m.clear_reactions()

        users = await self.executesql('SELECT COUNT(*) FROM leaderboards WHERE score > ? AND event_id = ? AND server_id = ?', (score, eventid, ctx.guild.id))
        items = await self.executesql('SELECT SUM(count) FROM inventories WHERE event_id = ? AND server_id = ? AND user_id = ?', (eventid, ctx.guild.id, ctx.author.id))

        embed = discord.Embed(title=f'You are in #{users[0][0] + 1} place!',
                              description=f'You have collected {items[0][0]} items so far, totalling {score} points! Keep it up!',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        embed.set_thumbnail(url=ctx.author.avatar_url_as())
        await m.edit(embed=embed)

    @leaderboard.command(name='help', help='full help for leaderboard commands')
    async def help(self, ctx, command):
        commandhelp = {"leaderboard": "`.leaderboard` or `.top10` will give you the list of the top 10 users this event!",
                       "myleaderboard": "`.myleaderboard [user]` will give you your current points and position this event, mentioning [user] will show your their position"}
        helpstr = commandhelp.get(command)
        if helpstr is None:
            await ctx.send('please enter a valid command, type `.leaderboard help` for a command list')
        else:
            embed = discord.Embed(colour=ctx.guild.get_member(self.bot.user.id).colour)
            embed.title = f'{command} help'
            embed.description = helpstr
            await ctx.send(embed=embed)

    async def position(self, ctx, m=None, *, username: discord.Member=None):
        sid = ctx.guild.id
        with open(f'cogs/leaderboards/lb{sid}.json', 'r') as file:
            d = json.loads(file.read())
        if username is None:
            if await Leaderboard.checkuser(self, ctx.message.author.id, d):
                lb = d['users']
                lb.sort(key=operator.itemgetter('points'), reverse=True)
                for i in range(len(lb)):
                    if lb[i]['userid'] == ctx.message.author.id:
                        embed = discord.Embed(colour=ctx.guild.get_member(self.bot.user.id).colour)
                        embed.title = f'you are in #{i+1} place!'
                        embed.description = 'you have collected {0} items so far, totalling {1} points! keep it up!'.format(await calculateItems(lb[i]['images']), lb[i]['points'])
                        embed.set_thumbnail(url=ctx.message.author.avatar_url_as())
                        if m is None:
                            return await ctx.send(embed=embed)
                        return await m.edit(embed=embed)
            await ctx.send('you haven\'t collected anything this event!')
        else:
            if await Leaderboard.checkuser(self, username.id, d):
                lb = d['users']
                lb.sort(key=operator.itemgetter('points'), reverse=True)
                for i in range(len(lb)):
                    if lb[i]['userid'] == username.id:
                        embed = discord.Embed(colour=ctx.guild.get_member(self.bot.user.id).colour)
                        embed.title = f'{username.display_name} is #{i+1} place!'
                        embed.description = 'they have collected {0} items so far, totalling {1} points!'.format(await calculateItems(lb[i]['images']), lb[i]['points'])
                        embed.set_thumbnail(url=username.avatar_url_as())
                        if m is None:
                            return await ctx.send(embed=embed)
                        return await m.edit(embed=embed)
            await ctx.send(f'{username.display_name} has\'t collected anything this event!')

    async def getlb(self, ctx, m):
        sid = ctx.guild.id
        with open(f'cogs/leaderboards/lb{sid}.json', 'r') as file:
            d = json.loads(file.read())
        lb = d['users']
        lb.sort(key=operator.itemgetter('points'), reverse=True)
        lbtxt = ''
        if len(lb) == 0:
            embed = discord.Embed(title='Leaderboard',
                                  description='There are no users on this leaderboard',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)
            return await m.edit(embed=embed)
        if len(lb) < 10:
            x = len(lb)
        else:
            x = 10

        for i in range(x):
            uid = await self.bot.fetch_user(lb[i]['userid'])
            lbtxt += '{0}. **{1}** - {2}\n'.format(i+1, uid.display_name, lb[i]['points'])
        embed = discord.Embed(colour=ctx.guild.get_member(self.bot.user.id).colour)
        embed.title = f'The top {x} users'
        embed.description = lbtxt
        return await m.edit(embed=embed)


    async def addpoint(self, uid, sid, image, points):
        with open(f'cogs/leaderboards/lb{sid}.json', 'r') as file:
            d = json.loads(file.read())
        updated = await Leaderboard.adduser(self, uid, image, d, points)
        if updated is None:
            for i, user in enumerate(d['users']):
                if user['userid'] == uid:
                    user['points'] += points
                    c = await Leaderboard.checkimage(self, uid, sid, image)
                    if c:
                        for im in user['images']:
                            if im['name'] == image:
                                im['count'] += 1
                                break
                    else:
                        user['images'].append({'name': image,
                                               'count': 1})
                    break
        else:
            d = updated
        with open(f'cogs/leaderboards/lb{sid}.json', 'w') as file:
            json.dump(d, file)


    async def adduser(self, uid, image, data, points):
        c = await Leaderboard.checkuser(self, uid, data)
        if c:
            return None
        else:
            data['users'].append({"userid": uid,
                                  "points": points,
                                  "images": [{'name': image,
                                              'count': 1}]})
            return data

    async def checkuser(self, userid, data):
        for user in data['users']:
            if user['userid'] == userid:
                return True
        return False

    async def checkimage(self, uid, sid, image):
        with open(f'cogs/leaderboards/lb{sid}.json', 'r') as file:
            d = json.loads(file.read())
        for user in d['users']:
            if user['userid'] == uid:
                for i in user['images']:
                    if i['name'].lower() == image.lower():
                        return True
        return False

    @leaderboard.command(name='clear', help='clears the leaderboard', hidden=True)
    @checkers.is_plant_owner()
    async def clearlb(self, ctx):
        cleared = {"users": []}
        with open(f'cogs/leaderboards/lb{ctx.guild.id}.json', 'w') as file:
            json.dump(cleared, file)

    # ------------- Error handling ------------- #

    @help.error
    async def helperror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            embed = discord.Embed(colour=ctx.guild.get_member(self.bot.user.id).colour)
            embed.title = 'please format this command as .leaderboard help [command]'
            embed.description = """leaderboard commands are:
            **leaderboard**: lists the top 10 users this event
            **myleaderboard**: displays your position and points this event"""
            await ctx.send(embed=embed)

class AnimeLeaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(help='anime leaderboard related commands', hidden=True)
    async def ani(self, ctx):
        if ctx.invoked_subcommand is None:
            await AnimeLeaderboard.getlb(self, ctx)
            return

    async def getlb(self, ctx, m=None):
        sid = ctx.guild.id
        with open(f'cogs/leaderboards/a{sid}.json', 'r') as file:
            d = json.loads(file.read())
        lb = d['users']
        lb.sort(key=operator.itemgetter('points'), reverse=True)
        lbtxt = ''
        if len(lb) == 0:
            embed = discord.Embed(title='Leaderboard',
                                  description='There are no users on this leaderboard',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)
            return await m.edit(embed=embed)
        elif len(lb) < 10:
            x = len(lb)
        else:
            x = 10

        for i in range(x):
            uid = await self.bot.fetch_user(lb[i]['userid'])
            lbtxt += '{0}. **{1}** - {2}\n'.format(i+1, uid.display_name, lb[i]['points'])
        embed = discord.Embed(colour=ctx.guild.get_member(self.bot.user.id).colour)
        embed.title = f'The top {x} users'
        embed.description = lbtxt
        if m is None:
            return await ctx.send(embed=embed)
        return await m.edit(embed=embed)

    async def position(self, ctx, m=None,  *, username: discord.Member=None):
        sid = ctx.guild.id
        with open(f'cogs/leaderboards/a{sid}.json', 'r') as file:
            d = json.loads(file.read())
        if username is None:
            if await Leaderboard.checkuser(self, ctx.message.author.id, d):
                lb = d['users']
                lb.sort(key=operator.itemgetter('points'), reverse=True)
                for i in range(len(lb)):
                    if lb[i]['userid'] == ctx.message.author.id:
                        embed = discord.Embed(colour=ctx.guild.get_member(self.bot.user.id).colour)
                        embed.title = f'you are in #{i+1} place!'
                        embed.description = 'you have collected {0} characters so far, totalling {1} points! keep it up!'.format(len(lb[i]['images']), lb[i]['points'])
                        embed.set_thumbnail(url=ctx.message.author.avatar_url_as())
                        if m is None:
                            return await ctx.send(embed=embed)
                        return await m.edit(embed=embed)
            await ctx.send('you haven\'t collected anything this event!')
        else:
            if await Leaderboard.checkuser(self, username.id, d):
                lb = d['users']
                lb.sort(key=operator.itemgetter('points'), reverse=True)
                for i in range(len(lb)):
                    if lb[i]['userid'] == username.id:
                        embed = discord.Embed()
                        embed.title = f'{username.display_name} is #{i+1} place!'
                        embed.description = 'they have collected {0} characters so far, totalling {1} points!'.format(len(lb[i]['images']), lb[i]['points'])
                        embed.set_thumbnail(url=username.avatar_url_as())
                        if m is None:
                            return await ctx.send(embed=embed)
                        return await m.edit(embed=embed)
            await ctx.send(f'{username.display_name} has\'t collected anything this event!')

    async def addpoint(self, uid, sid, imageurl, imagename, points):
        with open(f'cogs/leaderboards/a{sid}.json', 'r') as file:
            d = json.loads(file.read())
        temp = d
        updated = await AnimeLeaderboard.adduser(self, uid, imageurl, imagename, points,  d)
        if updated is None:
            for i, user in enumerate(d['users']):
                if user['userid'] == uid:
                    user['images'].append({"name": imagename,
                                           "url": imageurl})
                    user['points'] += points
                    break
            temp = d
        else:
            temp = updated
        with open(f'cogs/leaderboards/a{sid}.json', 'w') as file:
            json.dump(temp, file)
        return temp

    async def adduser(self, uid, imageurl, imagename, points, data):
        if await Leaderboard.checkuser(self, uid, data):
            print('user found')
            return None
        else:
            data['users'].append({"userid": uid,
                                  "points": points,
                                  "images": [{"name": imagename,
                                              "url": imageurl}]})
            return data

    def checkimage(self, uid, sid, name):
        with open(f'cogs/leaderboards/a{sid}.json', 'r') as file:
            d = json.loads(file.read())
        for user in d['users']:
            if user['userid'] == uid:
                for image in user['images']:
                    if image['name'].lower() == name.lower():
                        return True
        return False

    @ani.command(name='clear', help='clears the leaderboard', hidden=True)
    @checkers.is_guild_owner()
    async def clearlb(self, ctx):
        cleared = {"users": []}
        with open(f'cogs/leaderboards/a{ctx.guild.id}.json', 'w') as file:
            json.dump(cleared, file)

async def calculateItems(inventory):
    temp = 0
    for item in inventory:
        temp += item['count']
    return temp

def setup(bot):
    bot.add_cog(Leaderboard(bot))
    bot.add_cog(AnimeLeaderboard(bot))


