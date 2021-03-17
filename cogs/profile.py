#profile.py

import json
import discord
import asyncio

from discord.ext import commands
from datetime import date
from cogs import leaderboard


class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.store = 'randomImages'

    @commands.group(help='please use .profile help for more help!')
    async def profile(self, ctx):
        if ctx.invoked_subcommand is None:
            if len(ctx.message.mentions) == 0:
                await Profile.getprofile(self, ctx)
            else:
                await Profile.getprofile(self, ctx, ctx.message.mentions[0])
            return

    @profile.command(name='help', help='full help for leaderboard commands')
    async def help(self, ctx, command):
        commandhelp = {"profile": "```.profile [mention]``` will display your (or somebody you mention's) profile",
                       "setbio": "```.profile setbio [desc]``` will set your bio to ``[desc]``",
                       "setpronouns": "```.profile setpronouns [pronouns]``` will set your pronouns to ``[pronouns]``",
                       "setsexuality": "```.profile setsexuality [sexuality]``` will set your sexuality to ``[sexuality]``",
                       "setimage": "```.profile setimage [desc]``` will set your display to the image named ``[desc]`` if you own it",
                       "rep": "```.rep [mention]``` will give a rep to the user you mention, this command has a 12 hour cooldown",
                       "marry": "```.marry [mention]``` will allow you to marry a user you've mentioned (with their consent)",
                       "divorce":"```.divorce [mention]``` will allow you to divorce a user you've married (with their consent)"}
        helpstr = commandhelp.get(command)
        if helpstr is None:
            await ctx.send('please enter a valid command, type ``.profile help`` for a command list')
        else:
            embed = discord.Embed()
            embed.title = f'{command} help'
            embed.description = helpstr
            await ctx.send(embed=embed)


    @profile.command(name='profile', help='displays your profile')
    async def getprofile(self, ctx, at: discord.Member=None):
        if at is None:
            u = ctx.message.author
        else:
            u = at
        p = Profile.addprofile(self, u.id)

        embed = discord.Embed()
        embed.set_author(name='{0}\'s profile'.format(u.display_name), icon_url=u.avatar_url_as())
        embed.set_thumbnail(url=u.avatar_url_as())

        if p['bio'] is None:
            pass
        else:
            embed.add_field(name='\U0001F4AC Bio', value=p['bio'], inline=False)
        embed.add_field(name='\U0001F4AD Pronouns', value=Profile.processpronouns(self, p['pronouns']), inline=False)
        embed.add_field(name='\U0001F3C6 Total Points', value=p['points'])
        embed.add_field(name='\U0001F4A0 Rep', value=p['rep'])
        if p['sexuality'] is None:
            pass
        else:
            embed.add_field(name='\U0001F496 Sexuality', value=p['sexuality'], inline=False)
        if len(p['married']['users']) > 0:
            mstr = ''
            for i, user in enumerate(p['married']['users']):
                uname = await self.bot.fetch_user(p['married']['users'][i])
                mstr +='\U00002764 {0}: {1}\n'.format(uname, p['married']['dates'][i])
            embed.add_field(name='\U0001F48D Married to', value=mstr, inline=False)
        if p['image'] is None:
            pass
        else:
            embed.add_field(name='\U00002B50 Favourite Item', value=p['image']['desc'], inline=False)
            embed.set_image(url=p['image']['url'])
        embed.set_footer(text='Powered by chlorophyll <:leaf:817542552692457473>')
        return await ctx.send(embed=embed)

    @commands.command(name='marry', help='lets you marry another user')
    async def marry(self, ctx, user: discord.Member):
        if user == self.bot.user:
            return await ctx.send('thank you but the law doesn\'t recognise me as somebody you could marry...')
        if user == ctx.message.author:
            return await ctx.send('you can\'t marry yourself!')
        usr = ctx.message.author
        p0 = Profile.addprofile(self, usr.id)
        p1 = Profile.addprofile(self, user.id)

        with open('cogs/profiles.json', 'r') as file:
            d = json.loads(file.read())

        if len(p0['married']['users']) >= 5:
            return await ctx.send('you\'ve already married 5 people! i hope you signed a pre-nup...')
        elif len(p1['married']['users']) >= 5:
            return await ctx.send(f'{user.display_name} already married 5 people!')
        elif p0['married']['users'].count(user.id) == 1:
            return await ctx.send(f'you\'re already married to {user.display_name}!')
        else:
            await ctx.send(f'{user.mention}! {usr.mention} wants to marry you! do you accept? '
                           '[(y)es/(n)o]')
            def check(m):
                return m.channel == ctx.channel and m.author == user

            try:
                m = await self.bot.wait_for('message', check=check, timeout=60)
                if m.content.lower() in ['y', 'yes']:
                    p0['married']['users'].append(user.id)
                    p0['married']['dates'].append(date.today().strftime('%Y-%m-%d'))
                    p0.update({"married": {"users": p0['married']['users'],
                                           "dates": p0['married']['dates']}})
                    p1['married']['users'].append(usr.id)
                    p1['married']['dates'].append(date.today().strftime('%Y-%m-%d'))
                    p1.update({"married": {"users": p1['married']['users'],
                                           "dates": p1['married']['dates']}})
                    for i, u in enumerate(d['users']):
                        if u['userid'] == usr.id:
                            d['users'][i].update(p0)
                        if u['userid'] == user.id:
                            d['users'][i].update(p1)
                    with open('cogs/profiles.json', 'w') as file:
                        json.dump(d, file)
                    return await ctx.send('congratulations! you\'re now married!')
                if m.content.lower() in ['n', 'no']:
                    return await ctx.send('oh no! rejection! better luck next time!')
            except asyncio.TimeoutError:
                    return await ctx.send(f'uh oh, it seems like {user.mention} is busy, try again later!')

    @commands.command(name='divorce', help='lets you divorce another user')
    async def divorce(self, ctx, user: discord.Member):
        if user == self.bot.user:
            return await ctx.send('y-you mean, you want to break up with me...?')

        usr = ctx.message.author
        p0 = Profile.addprofile(self, usr.id)
        p1 = Profile.addprofile(self, user.id)

        with open('cogs/profiles.json', 'r') as file:
            d = json.loads(file.read())

        if p0['married']['users'].count(user.id) == 0:
            return await ctx.send(f'you aren\'t married to {user.display_name}!')
        else:
            await ctx.send(f'{user.mention}! {usr.mention} wants to divorce you! do you accept? '
                           '[(y)es/(n)o]')
            def check(m):
                return m.channel == ctx.channel and m.author == user

            try:
                m = await self.bot.wait_for('message', check=check, timeout=60)
                if m.content.lower() in ['y', 'yes']:
                    p0n = p0['married']['users'].index(user.id)
                    p0['married']['users'].pop(p0n)
                    p0['married']['dates'].pop(p0n)
                    p1n = p1['married']['users'].index(usr.id)
                    p1['married']['users'].pop(p1n)
                    p1['married']['dates'].pop(p1n)
                    p0.update({"married": {"users": p0['married']['users'],
                                           "dates": p0['married']['dates']}})
                    p1.update({"married": {"users": p1['married']['users'],
                                           "dates": p1['married']['dates']}})
                    for i, u in enumerate(d['users']):
                        if u['userid'] == usr.id:
                            d['users'][i].update(p0)
                        if u['userid'] == user.id:
                            d['users'][i].update(p1)
                    with open('cogs/profiles.json', 'w') as file:
                        json.dump(d, file)
                    return await ctx.send('you are now divorced :(')
                if m.content.lower() in ['n', 'no']:
                    return await ctx.send(f'it seems like {user.mention} wants to keep working on things')
            except asyncio.TimeoutError:
                return await ctx.send(f'uh oh, it seems like {user.mention} is busy, try again later!')

    @commands.command(name='rep', help='give another user rep')
    @commands.cooldown(1, 43200, commands.BucketType.user)
    async def rep(self, ctx, user: discord.Member):
        if user == self.bot.user:
            await ctx.send('thank you but you should save that for somebody special')
            return ctx.command.reset_cooldown(ctx)
        if user == ctx.message.author:
            await ctx.send('you cannot rep yourself!')
            return ctx.command.reset_cooldown(ctx)
        p = Profile.addprofile(self, user.id)

        with open('cogs/profiles.json', 'r') as file:
            d = json.loads(file.read())

        for i, u in enumerate(d['users']):
            if u['userid'] == user.id:
                d['users'][i].update({"rep": u['rep'] + 1})
                break
        with open('cogs/profiles.json', 'w') as file:
            json.dump(d, file)
        await ctx.send(f'you gave {user.display_name} a rep!')

    @profile.command(name='setbio', help='sets your profile description')
    async def setbio(self, ctx, *, desc):
        u = ctx.message.author
        p = Profile.addprofile(self, u.id)

        with open('cogs/profiles.json', 'r') as file:
            d = json.loads(file.read())

        temp = {"bio": desc}

        for i, user in enumerate(d['users']):
            if user['userid'] == u.id:
                d['users'][i].update(temp)
        with open('cogs/profiles.json', 'w') as file:
            json.dump(d, file)

        await ctx.send('bio set')

    @profile.command(name='setpronouns', help='sets your pronouns')
    async def setpronouns(self, ctx, *, pronouns):
        u = ctx.message.author
        Profile.addprofile(self, u.id)

        with open('cogs/profiles.json', 'r') as file:
            d = json.loads(file.read())
        temp = {"pronouns": pronouns}

        for i, user in enumerate(d['users']):
            if user['userid'] == u.id:
                d['users'][i].update(temp)
                break
        with open('cogs/profiles.json', 'w') as file:
            json.dump(d, file)

        await ctx.send('pronouns set')

    @profile.command(name='setsexuality', help='sets your sexuality')
    async def setsexuality(self, ctx, *, s):
        u = ctx.message.author
        Profile.addprofile(self, u.id)

        with open('cogs/profiles.json', 'r') as file:
            d = json.loads(file.read())
        temp = {"sexuality": s}

        for i, user in enumerate(d['users']):
            if user['userid'] == u.id:
                d['users'][i].update(temp)
                break
        with open('cogs/profiles.json', 'w') as file:
            json.dump(d, file)

        await ctx.send('sexuality set')

    @profile.command(name='setimage', help='sets a display image')
    async def setimage(self, ctx, *, image):
        u = ctx.message.author

        if leaderboard.Leaderboard.checkimage(self, u.id, ctx.guild.id, image):
            with open('cogs/profiles.json', 'r') as file:
                p = json.loads(file.read())
            with open(f'cogs/{self.store}.json', 'r') as file:
                d = json.loads(file.read())

            for im in d['images']:
                if im['desc'] == image:
                    temp = {"image": {"url": im['url'], "desc": image}}
                    break
            for i, user in enumerate(p['users']):
                if user['userid'] == u.id:
                    p['users'][i].update(temp)
                    break
            with open('cogs/profiles.json', 'w') as file:
                json.dump(p, file)
            await ctx.send('image set')
        else:
            await ctx.send('you don\'t have that item yet!')

    def addprofile(self, uid):
        with open('cogs/profiles.json', 'r') as file:
            d = json.loads(file.read())
        temp = d

        pc = Profile.checkprofile(self, uid, d)
        if pc is None:
            pc = {"userid": uid,
                  "pronouns": None,
                  "bio": None,
                  "sexuality": None,
                  "points": 0,
                  "rep": 0,
                  "married": {"users": [], "dates": []},
                  "image": None}
            temp["users"].append(pc)
            with open('cogs/profiles.json', 'w') as file:
                json.dump(temp, file)
        return pc

    def checkprofile(self, uid, d):
        for user in d['users']:
            if user['userid'] == uid:
                return user
        return None

    def processpronouns(self, pronouns):
        if pronouns is None:
            return "this user hasn't set their pronouns yet, please ask them for theirs before using any!"
        else:
            return pronouns

    async def addpoint(self, uid, p):
        Profile.addprofile(self, uid)
        with open(f'cogs/profiles.json', 'r') as file:
            d = json.loads(file.read())
        temp = d
        for i, user in enumerate(d['users']):
            if user['userid'] == uid:
                temp['users'][i].update({"points": user['points'] + p})
                break

        with open(f'cogs/profiles.json', 'w') as file:
            json.dump(temp, file)


# -------------- Error handling -------------- #

    @help.error
    async def helperror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            embed = discord.Embed()
            embed.title = 'please format this command as .profile help [command]'
            embed.description = """profile commands are:
            **profile**: posts your profile
            **setbio**: sets your bio
            **setpronouns**: sets your pronouns
            **setsexuality**: sets your sexuality
            **setimage**: sets a display image
            **rep**: gifts a rep to another user
            **marry**: lets you marry another user
            **divorce**: lets you divorce a user you've married"""

            await ctx.send(embed=embed)

    @setpronouns.error
    async def setpronounserror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send('please format as ```.profile setpronouns [pronouns]```')

    @setbio.error
    async def setbioerror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send('please format as ```.profile setbio [description]```')

    @setimage.error
    async def setimageerror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send('please format as ```.profile setimage [description]```')

    @setsexuality.error
    async def setsexualityerror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send('please format as ```.profile setsexuality [sexuality]```')

    @rep.error
    async def reperror(self, ctx, error):
        if isinstance(error, commands.errors.CommandOnCooldown):
            t = ctx.command.get_cooldown_retry_after(ctx)
            m, s = divmod(t, 60)
            h, m = divmod(m, 60)
            if m == 0:
                await ctx.send(f'you are currently on cooldown, please try again in {s:g} seconds')
            elif h == 0:
                await ctx.send(f'you are currently on cooldown, please try again in {m:g} minutes')
            else:
                await ctx.send(f'you are currently on cooldown, please try again in {h:g} hours and  {m:g} minutes')
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send('please format as ```.rep [mention]```')
            ctx.command.reset_cooldown(ctx)
