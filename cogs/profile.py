#profile.py

import json

import discord
import asyncio

from discord.ext import commands, tasks
from datetime import date
from cogs import leaderboard, badges
from aiosqlite import connect

from json import loads
from re import search, findall
from sqlite3 import connect
from datetime import datetime


class Profile(commands.Cog):
    version = '0.1'
    def __init__(self, bot):
        self.bot = bot
        self.store = 'randomImages'
        self.setup.start()

        self.executeSQL("PRAGMA foreign_keys = ON")

        self.executeSQL("""
                    CREATE TABLE IF NOT EXISTS fields (
                        field_id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        type INTEGER NOT NULL,
                        name TEXT,
                        data TEXT NOT NULL
                    )
                """)

        self.executeSQL("""
                    CREATE TABLE IF NOT EXISTS relationships (
                        relationship_id INTEGER PRIMARY KEY,
                        user_a_id INTEGER NOT NULL,
                        user_b_id INTEGER NOT NULL,
                        type INTEGER NOT NULL
                    )
                """)

        self.executeSQL("""
                    CREATE TABLE IF NOT EXISTS marriages (
                        marriage_id INTEGER PRIMARY KEY,
                        user_a_id INTEGER NOT NULL,
                        user_b_id INTEGER NOT NULL
                    )
                """)

    conn = connect("database.db")
    cursor = conn.cursor()

    WIZARD_EMOJIS = {
        "0":                    "0️⃣",
        "1":                    "1️⃣",
        "2":                    "2️⃣",
        "3":                    "3️⃣",
        "4":                    "4️⃣",
        "5":                    "5️⃣",
        "new":                  "🆕",
        "record_button":        "⏺️",
        "asterisk":             "*️⃣",
        "regional_indicator_p": "🇵",
        "eject":                "⏏️",
    }

    COLOUR_REGEX = "(#([0-9A-Fa-f]{3}){1,2})"

    def executeSQL(self, statement, data = ()):

        self.cursor.execute(statement, data)
        self.conn.commit()
        return self.cursor.fetchall()


    @tasks.loop(count=1)
    async def setup(self):
        await self.executesql("PRAGMA foreign_keys = ON")

    async def executesql(self, statement, data=()):
        db = await connect('database.db')
        cursor = await db.execute(statement, data)
        await db.commit()
        rows = await cursor.fetchall()
        await cursor.close()
        await db.close()
        return list(rows)


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
        commandhelp = {"profile": "`.profile [mention]` will display your (or somebody you mention's) profile",
                       "setbio": "`.profile setbio [desc]` will set your bio to `[desc]`",
                       "setpronouns": "`.profile setpronouns [pronouns]` will set your pronouns to `[pronouns]`",
                       "setsexuality": "`.profile setsexuality [sexuality]` will set your sexuality to `[sexuality]`",
                       "setimage": "`.profile setimage [desc]` will set your display to the image named `[desc]` if you own it",
                       "setbadge": "`.profile setbadge [badge]` will add [badge] to your profile",
                       "rep": "`.rep [mention]` will give a rep to the user you mention, this command has a 12 hour cooldown",
                       "marry": "`.marry [mention]` will allow you to marry a user you've mentioned (with their consent)",
                       "divorce":"`.divorce [mention]` will allow you to divorce a user you've married"}
        helpstr = commandhelp.get(command)
        if helpstr is None:
            await ctx.send('please enter a valid command, type `.profile help` for a command list')
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
        if p['badges']:
            temp = ""
            for i in p['badges']:
                temp += i + '\U000000A0'
            embed.add_field(name='\U0001F451 Badges', value=temp, inline=False)
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
        embed.set_footer(text='Powered by chlorophyll')
        return await ctx.send(embed=embed)

    @commands.command(name='marry', help='lets you marry another user')
    async def marry(self, ctx, user: discord.Member):
        if ctx.guild.id == 502944697225052181:
            return await ctx.send('This feature is disabled on this server')
        elif await self.checkblacklist(ctx.message.author.id):
            return await ctx.send('You are currently blacklisted from using this command')
        elif await self.checkblacklist(user.id):
            return await ctx.send(f'{user.mention} is currently blacklisted from using this command')
        elif user == self.bot.user:
            return await ctx.send('thank you but the law doesn\'t recognise me as somebody you could marry...')
        elif user == ctx.message.author:
            return await ctx.send('you can\'t marry yourself!')
        usr = ctx.message.author
        p0 = Profile.addprofile(self, usr.id)
        p1 = Profile.addprofile(self, user.id)

        with open('cogs/profiles.json', 'r') as file:
            d = json.loads(file.read())

        if len(p0['married']['users']) >= 5 and p0['userid'] != 579785620612972581:
            return await ctx.send('you\'ve already married 5 people! i hope you signed a pre-nup...')
        elif len(p1['married']['users']) >= 5 and p1['userid'] != 579785620612972581:
            return await ctx.send(f'{user.display_name} already married 5 people!')
        elif p0['married']['users'].count(user.id) == 1:
            return await ctx.send(f'you\'re already married to {user.display_name}!')
        else:
            await ctx.send(f'{user.mention}! {usr.mention} wants to marry you! do you accept? '
                           '[(y)es/(n)o]')
            def check(m):
                return m.channel == ctx.channel and m.author == user

            try:
                while True:
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
        if ctx.guild.id == 502944697225052181:
            return await ctx.send('This feature is disabled on this server')
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

    @profile.command(name='set', hidden=True)
    async def set(self, ctx, *, args):
        if 'bio' in args.lower():
            return await ctx.send('the correct format is `.profile setbio [bio]`')
        if 'pronouns' in args.lower():
            return await ctx.send('the correct format is `.profile setpronouns [pronouns]`')
        if 'image' in args.lower():
            return await ctx.send('the correct format is `.profile setimage [image name]`')
        if 'sexuality' in args.lower():
            return await ctx.send('the correct format is `.profile setsexuality [sexuality]')
        if 'badge' in args.lower():
            return await ctx.send('the correct format is `.profile setbadge [badge]`')
        else:
            return await ctx.send('i don\'t recognise that command, please use `.profile help` for more information about profile commands')

    @profile.command(name='setbio', help='sets your profile description')
    async def setbio(self, ctx, *, desc):
        u = ctx.message.author
        Profile.addprofile(self, u.id)

        if len(desc) > 1024:
            return await ctx.send('this bio is too long, please make sure it is fewer than 1024 characters')

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

        if len(pronouns) > 1024:
            return await ctx.send('these pronouns are too long, please make sure it is fewer than 1024 characters')

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

        if len(s) > 1024:
            return await s.send('this bio is too long, please make sure it is fewer than 1024 characters')

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
        Profile.addprofile(self, u.id)
        with open('cogs/profiles.json', 'r') as file:
            p = json.loads(file.read())
        temp = None

        if await leaderboard.Leaderboard.checkimage(self, u.id, ctx.guild.id, image):
            with open(f'cogs/{self.store}.json', 'r') as file:
                d = json.loads(file.read())

            for im in d['images']:
                if im['desc'].lower() == image.lower():
                    temp = {"image": {"url": im['url'], "desc": image}}
                    break
            if temp is None:
                with open(f'cogs/flowers.json', 'r') as file:
                    f = json.loads(file.read())
                for cat in f:
                    for flower in f[cat]:
                        t = list(flower.items())
                        if t[0][0].lower() == image.lower():
                            temp = {"image": {"url": t[0][1], "desc": t[0][0]}}
                            break
            for i, user in enumerate(p['users']):
                if user['userid'] == u.id:
                    p['users'][i].update(temp)
                    break
            with open('cogs/profiles.json', 'w') as file:
                json.dump(p, file)
            return await ctx.send('image set')
        elif leaderboard.AnimeLeaderboard.checkimage(self, u.id, ctx.guild.id, image):
            with open(f'cogs/leaderboards/a{ctx.guild.id}.json', 'r') as file:
                a = json.loads(file.read())
            for user in a['users']:
                if user['userid'] == u.id:
                    for im in user['images']:
                        if im['name'].lower() == image.lower():
                            temp = {"image": {"url": im['url'], "desc": im['name']}}
                            break
            for i, user in enumerate(p['users']):
                if user['userid'] == u.id:
                    p['users'][i].update(temp)
                    break
            with open('cogs/profiles.json', 'w') as file:
                json.dump(p, file)
            return await ctx.send('image set')
        dbcheck = await self.executesql('SELECT im.text, im.url FROM inventories inv INNER JOIN images im USING (image_id) WHERE (im.event_id = ? AND inv.user_id = ? AND inv.server_id = ? AND lower(im.text) = ?)', (1, ctx.author.id, ctx.guild.id, image))
        if len(dbcheck):
            temp = {"image": {"url": dbcheck[0][1], "desc": dbcheck[0][0]}}
            for i, user in enumerate(p['users']):
                if user['userid'] == u.id:
                    p['users'][i].update(temp)
                    break
            with open('cogs/profiles.json', 'w') as file:
                json.dump(p, file)
            return await ctx.send('image set')
        else:
            return await ctx.send('you don\'t have that item yet!')

    @profile.command(name='setbadge', help='sets your profile badge')
    async def setbadge(self, ctx, *, badge):
        uid = ctx.message.author.id
        Profile.addprofile(self, uid)
        with open('cogs/badges.json', 'r') as file:
            d = json.loads(file.read())
        t = await badges.Badge.checkbadge(self, uid, badge, d)
        print(t)
        if t:
            with open('cogs/profiles.json', 'r') as file:
                p = json.loads(file.read())
            for user in p['users']:
                if user['userid'] == uid:
                    b = d['badges'].get(badge)
                    if user['badges'].count(b):
                        return await ctx.send('you\'ve already set this badge!')
                    user['badges'].append(b)
                    with open('cogs/profiles.json', 'w') as file:
                        json.dump(p, file)
                    return await ctx.send('badge set!')
        return await ctx.send('you don\'t have that badge yet!')

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
                  "image": None,
                  "badges": []}
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

    async def checkblacklist(self, userid):
        with open(f'cogs/userblacklist.json', 'r') as file:
            d = json.loads(file.read())
        if d['id'].count(userid):
            return True
        return False


# -------------- Error handling -------------- #

    @help.error
    async def helperror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            embed = discord.Embed()
            embed.title = 'please format this command as .profile help [command] for more information'
            embed.add_field(name='Please format these commands as .profile [command]', value='**setbio**: sets your bio \n**setpronouns**: sets your pronouns \n**setsexuality**: sets your sexuality \n**setimage**: sets a display image\n**setbadge**: sets a badge to profile', inline=False)
            embed.add_field(name='Please format these commands as they are', value='**profile**: posts your profile\n**rep**: gifts a rep to another user\n**marry**: lets you marry another user\n**divorce**: lets you divorce a user you\'ve married', inline=False)
            await ctx.send(embed=embed)

    @setpronouns.error
    async def setpronounserror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send('please format as `.profile setpronouns [pronouns]`')

    @setbio.error
    async def setbioerror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send('please format as `.profile setbio [bio]`')

    @setimage.error
    async def setimageerror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send('please format as `.profile setimage [description]`')

    @setsexuality.error
    async def setsexualityerror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send('please format as `.profile setsexuality [sexuality]`')

    @setbadge.error
    async def setbadgeerror(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send('please format as `.profile setbadge [badge]`')

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
                await ctx.send(f'you are currently on cooldown, please try again in {h:g} hours and {m:g} minutes')
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send('please format as `.rep [mention]`')
            ctx.command.reset_cooldown(ctx)
        if isinstance(error, commands.BadArgument):
            await ctx.send('please format as `.rep [mention]`')
            ctx.command.reset_cooldown(ctx)

# -------------- New Profiles -------------- #

# -------  Matthew Hammond, 2021  ------
# ----  Profile Plant Bot Commands  ----
# ---------------  v1.0  ---------------


    @commands.command(
        name = "profilewizard",
        aliases = ["pwiz", "pw"],

        brief = "Create and edit your profile.",
        description = "Create and edit your profile! Add fields and showcase badges!",
    )
    async def profileWizard(self, ctx):

        embed = discord.Embed(
            title = "Profile Wizard",
            description = "Loading...",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        msg = await ctx.send(embed = embed)

        for emoji in self.WIZARD_EMOJIS.values():
            await msg.add_reaction(emoji)

        await self.mainMenu(ctx, msg)

        embed = discord.Embed(
            title = "Profile Wizard",
            description = "Finished.",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        await msg.edit(embed = embed)

    async def mainMenu(self, ctx, msg):

        def check(reaction, user):
            return ctx.author.id == user.id and msg.id == reaction.message.id

        availableFields = self.executeSQL("""
            SELECT field_id, type, name FROM fields
            WHERE user_id = ? AND type <> 0
        """, (ctx.author.id,))

        while True:

            embed = discord.Embed(
                title = "Profile Wizard - Edit your profile.",
                description = "React with a number to select a field.\nReact with :new: to create a new field.\nReact with :record_button: to edit your bio.\nReact with :asterisk: to reset your profile.\nReact with :regional_indicator_p: to preview your profile.\nReact with :eject: to quit.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            if (len(availableFields)):
                embed.add_field(
                    name = "Available Fields ({}/{})".format(len(availableFields), "5"),
                    value = "\n".join(self.WIZARD_EMOJIS[str(i)] + " " + str(availableFields[i][2]) for i in range(0, len(availableFields)))
                )
            else:
                embed.add_field(
                    name = "Available Fields (0/{})".format("5"),
                    value = "None",
                )
            await msg.edit(embed = embed)

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = check)
            except asyncio.TimeoutError:
                return
            await msg.remove_reaction(reaction, user)

            if (reaction.emoji == self.WIZARD_EMOJIS["new"]):
                await self.newField(ctx, msg)

                availableFields = self.executeSQL("""
                    SELECT field_id, type, name FROM fields
                    WHERE user_id = ? AND type <> 0
                """, (ctx.author.id,))

            elif (reaction.emoji == self.WIZARD_EMOJIS["record_button"]):
                await self.editBio(ctx, msg)

            elif (reaction.emoji == self.WIZARD_EMOJIS["asterisk"]):
                await self.resetProfile(ctx, msg)

                availableFields = self.executeSQL("""
                    SELECT field_id, type, name FROM fields
                    WHERE user_id = ? AND type <> 0
                """, (ctx.author.id,))

            elif (reaction.emoji == self.WIZARD_EMOJIS["regional_indicator_p"]):
                await self.previewProfile(ctx, msg)

            elif (reaction.emoji == self.WIZARD_EMOJIS["eject"]):
                return

            elif (reaction.emoji in self.WIZARD_EMOJIS.values()):
                if (int(reaction.emoji[0]) < len(availableFields)):
                    field = availableFields[int(reaction.emoji[0])]

                    if (field[1] == 1):
                        await self.textFieldMenu(ctx, msg, field[0])
                    elif (field[1] == 2):
                        await self.badgeFieldMenu(ctx, msg, field[0])
                    elif (field[1] == 3):
                        await self.imageFieldMenu(ctx, msg, field[0])
                    elif (field[1] == 4):
                        await self.colourFieldMenu(ctx, msg, field[0])

                    availableFields = self.executeSQL("""
                        SELECT field_id, type, name FROM fields
                        WHERE user_id = ? AND type <> 0
                    """, (ctx.author.id,))

    async def newField(self, ctx, msg):

        def check(reaction, user):
            return ctx.author.id == user.id and msg.id == reaction.message.id

        fieldCount = self.executeSQL("""
            SELECT COUNT(*) FROM fields
            WHERE user_id = ?
        """, (ctx.author.id,))[0][0]

        premiumUser = len(self.executeSQL("""
            SELECT premium_user_id FROM premium_users
            WHERE user_id = ?
        """, (ctx.author.id,)))

        if (fieldCount >= 2 and not premiumUser):
            embed = discord.Embed(
                title = "Profile Wizard - Add a field.",
                description = "You need premium to have more than 2 fields!\nReact with :eject: to go back.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            await msg.edit(embed = embed)

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = check)
            except asyncio.TimeoutError:
                return
            await msg.remove_reaction(reaction, user)
            return

        elif (fieldCount >= 5 and premiumUser):
            embed = discord.Embed(
                title = "Profile Wizard - Add a field.",
                description = "You cannot have more than 5 fields!\nReact with :eject: to go back.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            await msg.edit(embed = embed)

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = check)
            except asyncio.TimeoutError:
                return
            await msg.remove_reaction(reaction, user)
            return

        else:
            embed = discord.Embed(
                title = "Profile Wizard - Add a field.",
                description = "React with :zero: to create a text field.\nReact with :one: to create a badge showcase.\nReact with :two: to create an image showcase.\nReact with :three: to create a custom colour field.\nReact with :eject: to go back.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            await msg.edit(embed = embed)

            while True:

                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = check)
                except asyncio.TimeoutError:
                    return
                await msg.remove_reaction(reaction, user)

                if (reaction.emoji == self.WIZARD_EMOJIS["eject"]):
                    return

                elif (reaction.emoji == self.WIZARD_EMOJIS["0"]):
                    await self.newTextField(ctx, msg)
                    return

                elif (reaction.emoji == self.WIZARD_EMOJIS["1"]):
                    await self.newBadgeField(ctx, msg)
                    return

                elif (reaction.emoji == self.WIZARD_EMOJIS["2"]):
                    fieldId = await self.newImageField(ctx, msg)
                    if (fieldId):
                        await self.imageFieldMenu(ctx, msg, fieldId)
                    return

                elif (reaction.emoji == self.WIZARD_EMOJIS["3"]):
                    fieldId = await self.newColourField(ctx, msg)
                    if (fieldId):
                        await self.colourFieldMenu(ctx, msg, fieldId)
                    return

    async def newTextField(self, ctx, msg):

        def heading_check(msg):
            return ctx.author.id == msg.author.id and ctx.channel.id == msg.channel.id and len(msg.content) <= 32

        def content_check(msg):
            return ctx.author.id == msg.author.id and ctx.channel.id == msg.channel.id and len(msg.content) <= 512

        embed = discord.Embed(
            title = "Profile Wizard - Add a text field.",
            description = "Reply with the heading of the text field. (Max 32 characters)\nWait 60s to cancel.",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        await msg.edit(embed = embed)

        try:
            heading = await self.bot.wait_for("message", timeout = 60, check = heading_check)
        except asyncio.TimeoutError:
            return
        await heading.delete()
        heading = heading.content

        embed = discord.Embed(
            title = "Profile Wizard - Add a text field.",
            description = "Reply with the content of the text field. (Max 512 characters)\nWait 300s to cancel.",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        await msg.edit(embed = embed)

        try:
            content = await self.bot.wait_for("message", timeout = 300, check = content_check)
        except asyncio.TimeoutError:
            return
        await content.delete()
        content = content.content

        self.executeSQL("""
            INSERT INTO fields (user_id, type, name, data)
            VALUES (?, 1, ?, ?)
        """, (ctx.author.id, heading, content))

    async def textFieldMenu(self, ctx, msg, fieldId):

        def check(reaction, user):
            return user.id == ctx.author.id and reaction.emoji in self.WIZARD_EMOJIS.values()

        textField = self.executeSQL("""
            SELECT name, data FROM fields
            WHERE field_id = ?
        """, (fieldId,))[0]

        while True:

            embed = discord.Embed(
                title = "Profile Wizard - Edit a text field.",
                description = "React with :zero: to change the heading.\nReact with :one: to change the content.\nReact with :asterisk: to delete the field.\nReact with :eject: to go back.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            embed.add_field(name = textField[0], value = textField[1])
            await msg.edit(embed = embed)

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = check)
            except asyncio.TimeoutError:
                return
            await msg.remove_reaction(reaction, user)

            if (reaction.emoji == self.WIZARD_EMOJIS["eject"]):
                return

            elif (reaction.emoji == self.WIZARD_EMOJIS["asterisk"]):
                if (await self.deleteTextField(ctx, msg, fieldId)): return

            elif (reaction.emoji == self.WIZARD_EMOJIS["0"]):
                await self.editTextFieldHeading(ctx, msg, fieldId)
                textField = self.executeSQL("""
                    SELECT name, data FROM fields
                    WHERE field_id = ?
                """, (fieldId,))[0]

            elif (reaction.emoji == self.WIZARD_EMOJIS["1"]):
                await self.editTextFieldContent(ctx, msg, fieldId)
                textField = self.executeSQL("""
                    SELECT name, data FROM fields
                    WHERE field_id = ?
                """, (fieldId,))[0]

    async def editTextFieldHeading(self, ctx, msg, fieldId):

        def heading_check(msg):
            return ctx.author.id == msg.author.id and ctx.channel.id == msg.channel.id and len(msg.content) <= 32

        currentHeading = self.executeSQL("""
            SELECT name FROM fields
            WHERE field_id = ?
        """, (fieldId,))[0][0]

        embed = discord.Embed(
            title = "Profile Wizard - Edit a text field.",
            description = "Reply with the new heading of the text field. (Max 32 characters)\nWait 60s to cancel.",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        embed.add_field(name = "Current Heading", value = currentHeading)
        await msg.edit(embed = embed)

        try:
            heading = await self.bot.wait_for("message", timeout = 60, check = heading_check)
        except asyncio.TimeoutError:
            return
        await heading.delete()
        heading = heading.content

        self.executeSQL("""
            UPDATE fields
            SET name = ?
            WHERE field_id = ?
        """, (fieldId,))

    async def editTextFieldContent(self, ctx, msg, fieldId):

        def content_check(msg):
            return ctx.author.id == msg.author.id and ctx.channel.id == msg.channel.id and len(msg.content) <= 512

        currentContent = self.executeSQL("""
            SELECT data FROM fields
            WHERE field_id = ?
        """, (fieldId,))[0][0]

        embed = discord.Embed(
            title = "Profile Wizard - Edit a text field.",
            description = "Reply with the new content of the text field. (Max 512 characters)\nWait 60s to cancel.",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        embed.add_field(name = "Current Content", value = currentContent)
        await msg.edit(embed = embed)

        try:
            content = await self.bot.wait_for("message", timeout = 60, check = content_check)
        except asyncio.TimeoutError:
            return
        await content.delete()
        content = content.content

        self.executeSQL("""
            UPDATE fields
            SET data = ?
            WHERE field_id = ?
        """, (fieldId,))

    async def deleteTextField(self, ctx, msg, fieldId):

        def check(msg):
            return ctx.author.id == msg.author.id and ctx.channel.id == msg.channel.id

        embed = discord.Embed(
            title = "Profile Wizard - Delete a text field.",
            description = "Are you sure? (Y/N)\n",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        await msg.edit(embed = embed)

        try:
            confirmation = await self.bot.wait_for("message", timeout = 60, check = check)
        except asyncio.TimeoutError:
            return False
        await confirmation.delete()

        if (confirmation.content.lower()[0] != "y"):
            return

        self.executeSQL("""
            DELETE FROM fields
            WHERE field_id = ?
        """, (fieldId,))

        return True

    async def newBadgeField(self, ctx, msg):

        def badge_check(msg):
            return ctx.author.id == msg.author.id and ctx.channel.id == msg.channel.id

        def check(r, u):
            return r.message == msg and u == ctx.author and r.emoji == self.WIZARD_EMOJIS['eject']

        embed = discord.Embed(
            title = "Profile Wizard - Add a badge showcase.",
            description = "Reply with the name of the badge you want to showcase.\nWait 60s to go back.",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        await msg.edit(embed = embed)

        try:
            badge = await self.bot.wait_for("message", timeout = 300, check = badge_check)
        except asyncio.TimeoutError:
            return False
        await badge.delete()
        badge = badge.content

        with open('cogs/badges.json', 'r') as file:
            data = loads(file.read())

        if (await badges.Badge.checkbadge(self, ctx.author.id, badge, data)):

            badge = data['badges'].get(badge)

            self.executeSQL("""
                INSERT INTO fields (user_id, type, name, data)
                VALUES (?, 2, "Badge Showcase", ?)
            """, (ctx.author.id, badge))

            self.badgeFieldMenu(ctx, msg, await self.badgeFieldMenu(ctx, msg, self.executeSQL("""
                SELECT field_id FROM fields
                WHERE user_id = ? AND type = 2
            """, (ctx.author.id,))[0][0]))

        else:
            embed = discord.Embed(
                title = "Profile Wizard - Add a badge showcase.",
                description = "You don't have that badge!\nReact with :eject: or wait 60s to go back.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            await msg.edit(embed = embed)

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = check)
            except asyncio.TimeoutError:
                return False
            await msg.remove_reaction(reaction, user)
            return False

    async def badgeFieldMenu(self, ctx, msg, fieldId):

        def check(reaction, user):
            return user.id == ctx.author.id and reaction.emoji in self.WIZARD_EMOJIS.values()

        badge = self.executeSQL("""
            SELECT data FROM fields
            WHERE field_id = ?
        """, (fieldId,))[0][0]

        while True:

            embed = discord.Embed(
                title = "Profile Wizard - Edit a badge showcase.",
                description = "React with :zero: to change the badge.\nReact with :asterisk: to delete the showcase.\nReact with :eject: to go back.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            embed.add_field(name = "Badge", value = badge)
            await msg.edit(embed = embed)

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = check)
            except asyncio.TimeoutError:
                return
            await msg.remove_reaction(reaction, user)

            if (reaction.emoji == self.WIZARD_EMOJIS["eject"]):
                return

            elif (reaction.emoji == self.WIZARD_EMOJIS["asterisk"]):
                if (await self.deleteBadgeField(ctx, msg, fieldId)): return

            elif (reaction.emoji == self.WIZARD_EMOJIS["0"]):
                await self.editBadgeFieldBadge(ctx, msg, fieldId)
                badge = self.executeSQL("""
                    SELECT data FROM fields
                    WHERE field_id = ?
                """, (fieldId,))[0][0]

    async def editBadgeFieldBadge(self, ctx, msg, fieldId):

        def check(reaction, user):
            return user.id == ctx.author.id and reaction.emoji in self.WIZARD_EMOJIS.values()

        def badge_check(msg):
            return ctx.author.id == msg.author.id and ctx.channel.id == msg.channel.id

        badge = self.executeSQL("""
            SELECT data FROM fields
            WHERE field_id = ?
        """, (fieldId,))[0][0]

        embed = discord.Embed(
            title = "Profile Wizard - Edit a badge showcase.",
            description = "Reply with the name of the badge you want to showcase.\nWait 60s to go back.",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        embed.add_field(name = "currentBadge", value = badge)
        await msg.edit(embed = embed)

        try:
            badge = await self.bot.wait_for("message", timeout = 300, check = badge_check)
        except asyncio.TimeoutError:
            return False
        await badge.delete()
        badge = badge.content

        with open('cogs/badges.json', 'r') as file:
            data = loads(file.read())

        if (await badges.Badge.checkbadge(self, ctx.author.id, badge, data)):

            badge = data['badges'].get(badge)

            self.executeSQL("""
                UPDATE fields
                SET data = ?
                WHERE field_id = ?
            """, (badge, fieldId))

        else:
            embed = discord.Embed(
                title = "Profile Wizard - Add a badge showcase.",
                description = "You don't have that badge!\nReact with :eject: or wait 60s to go back.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            await msg.edit(embed = embed)

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = check)
            except asyncio.TimeoutError:
                return
            await msg.remove_reaction(reaction, user)

    async def deleteBadgeField(self, ctx, msg, fieldId):

        def check(msg):
            return ctx.author.id == msg.author.id and ctx.channel.id == msg.channel.id

        embed = discord.Embed(
            title = "Profile Wizard - Delete a badge showcase.",
            description = "Are you sure? (Y/N)\n",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        await msg.edit(embed = embed)

        try:
            confirmation = await self.bot.wait_for("message", timeout = 60, check = check)
        except asyncio.TimeoutError:
            return False
        await confirmation.delete()

        if (confirmation.content.lower()[0] != "y"):
            return

        self.executeSQL("""
            DELETE FROM fields
            WHERE field_id = ?
        """, (fieldId,))

        return True

    async def newImageField(self, ctx, msg, fieldId = 0):

        def check(reaction, user):
            return ctx.author.id == user.id and msg.id == reaction.message.id

        def image_check(msg):
            return ctx.author.id == msg.author.id and ctx.channel.id == msg.channel.id

        hasField = len(self.executeSQL("""
            SELECT field_id FROM fields
            WHERE user_id = ? AND type = 3 AND field_id <> ?
        """, (ctx.author.id, fieldId)))

        if (hasField):
            embed = discord.Embed(
                title = "Profile Wizard - Add an image showcase.",
                description = "You can't have more than 1 image!\nReact with :eject: to go back.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            await msg.edit(embed = embed)

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = check)
            except asyncio.TimeoutError:
                return
            await msg.remove_reaction(reaction, user)
            return

        embed = discord.Embed(
            title = "Profile Wizard - Add an image showcase.",
            description = "Reply with the name of the image you want to showcase.\nWait 60s to go back.",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        await msg.edit(embed = embed)

        try:
            image = await self.bot.wait_for("message", timeout = 300, check = image_check)
        except asyncio.TimeoutError:
            return False
        await image.delete()
        image = image.content

        if (await leaderboard.Leaderboard.checkimage(self, ctx.author.id, ctx.guild.id, image)):
            with open(f'cogs/randomImages.json', 'r') as file:
                d = json.loads(file.read())

            for im in d['images']:
                if im['desc'].lower() == image.lower():
                    temp = {"image": {"url": im['url'], "desc": image}}
                    break

            if temp is None:
                with open(f'cogs/flowers.json', 'r') as file:
                    f = json.loads(file.read())
                for cat in f:
                    for flower in f[cat]:
                        t = list(flower.items())
                        if t[0][0].lower() == image.lower():
                            temp = {"image": {"url": t[0][1], "desc": t[0][0]}}
                            break

            image = temp["image"]["url"]

        elif (leaderboard.AnimeLeaderboard.checkimage(self, ctx.author.id, ctx.guild.id, image)):
            with open(f'cogs/leaderboards/a{ctx.guild.id}.json', 'r') as file:
                a = json.loads(file.read())

            for user in a['users']:
                if user['userid'] == ctx.author.id:
                    for im in user['images']:
                        if im['name'].lower() == image.lower():
                            temp = {"image": {"url": im['url'], "desc": im['name']}}
                            break

            image = temp["image"]["url"]

        if (image == "hoot hoot"):
            image = "https://i.imgur.com/QSEH0xT.jpg"

        else:
            embed = discord.Embed(
                title = "Profile Wizard - Add an image showcase.",
                description = "You don't have that image!\nReact with :eject: or wait 60s to go back.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            await msg.edit(embed = embed)

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = check)
            except asyncio.TimeoutError:
                return False
            await msg.remove_reaction(reaction, user)
            return False

        if (fieldId):
            self.executeSQL("""
                UPDATE fields
                SET data = ?
                WHERE field_id = ?
            """, (image, fieldId))

        else:
            self.executeSQL("""
                INSERT INTO fields (user_id, type, name, data)
                VALUES (?, 3, "Image Showcase", ?)
            """, (ctx.author.id, image))

        return self.executeSQL("""
            SELECT field_id FROM fields
            WHERE user_id = ? AND type = 3
        """, (ctx.author.id,))[0][0]

    async def imageFieldMenu(self, ctx, msg, fieldId):

        def check(reaction, user):
            return user.id == ctx.author.id and reaction.emoji in self.WIZARD_EMOJIS.values()

        image = self.executeSQL("""
            SELECT data FROM fields
            WHERE field_id = ?
        """, (fieldId,))[0][0]

        while True:

            embed = discord.Embed(
                title = "Profile Wizard - Edit an image showcase.",
                description = "React with :zero: to change the image.\nReact with :asterisk: to delete the showcase.\nReact with :eject: to go back.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            embed.set_image(url = image)
            await msg.edit(embed = embed)

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = check)
            except asyncio.TimeoutError:
                return
            await msg.remove_reaction(reaction, user)

            if (reaction.emoji == self.WIZARD_EMOJIS["eject"]):
                return

            elif (reaction.emoji == self.WIZARD_EMOJIS["asterisk"]):
                if (await self.deleteImageField(ctx, msg, fieldId)): return

            elif (reaction.emoji == self.WIZARD_EMOJIS["0"]):
                await self.newImageField(ctx, msg, fieldId)
                image = self.executeSQL("""
                    SELECT data FROM fields
                    WHERE field_id = ?
                """, (fieldId,))[0][0]

    async def deleteImageField(self, ctx, msg, fieldId):

        def check(msg):
            return ctx.author.id == msg.author.id and ctx.channel.id == msg.channel.id

        embed = discord.Embed(
            title = "Profile Wizard - Delete an image showcase.",
            description = "Are you sure? (Y/N)\n",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        await msg.edit(embed = embed)

        try:
            confirmation = await self.bot.wait_for("message", timeout = 60, check = check)
        except asyncio.TimeoutError:
            return False
        await confirmation.delete()

        if (confirmation.content.lower()[0] != "y"):
            return

        self.executeSQL("""
            DELETE FROM fields
            WHERE field_id = ?
        """, (fieldId,))

        return True

    async def newColourField(self, ctx, msg, fieldId = 0):

        def check(reaction, user):
            return ctx.author.id == user.id and msg.id == reaction.message.id

        def colour_check(msg):
            return ctx.author.id == msg.author.id and ctx.channel.id == msg.channel.id and search(self.COLOUR_REGEX, msg.content)

        hasField = len(self.executeSQL("""
            SELECT field_id FROM fields
            WHERE user_id = ? AND type == 4 AND field_id <> ?
        """, (ctx.author.id, fieldId)))

        hasPremium = len(self.executeSQL("""
            SELECT premium_user_id FROM premium_users
            WHERE user_id = ?
        """, (ctx.author.id,)))

        if (hasField):
            embed = discord.Embed(
                title = "Profile Wizard - Add a custom colour.",
                description = "You can't have more than 1 custom colour!\nReact with :eject: to go back.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            await msg.edit(embed = embed)

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = check)
            except asyncio.TimeoutError:
                return
            await msg.remove_reaction(reaction, user)
            return

        elif (hasPremium):
            embed = discord.Embed(
                title = "Profile Wizard - Add a custom colour.",
                description = "You need premium to set a custom colour!\nReact with :eject: to go back.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            await msg.edit(embed = embed)

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = check)
            except asyncio.TimeoutError:
                return
            await msg.remove_reaction(reaction, user)
            return


        embed = discord.Embed(
            title = "Profile Wizard - Add a custom colour.",
            description = "Reply with the RGB code of the colour. (e.g #FFF or #FFFFFF)\nWait 60s to go back.",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        await msg.edit(embed = embed)

        try:
            colour = await self.bot.wait_for("message", timeout = 300, check = colour_check)
        except asyncio.TimeoutError:
            return False
        await colour.delete()
        colour = findall(self.COLOUR_REGEX, colour.content)[0][0]

        colour = colour[1:]
        if (len(colour) == 3):
            colour = colour[0] * 2 + colour[1] * 2 + colour[2] * 2

        if (fieldId):
            self.executeSQL("""
                UPDATE fields
                SET data = ?
                WHERE field_id = ?
            """, (colour, fieldId))

        else:
            self.executeSQL("""
                INSERT INTO fields (user_id, type, name, data)
                VALUES (?, 4, "Custom Colour", ?)
            """, (ctx.author.id, colour))

        return self.executeSQL("""
            SELECT field_id FROM fields
            WHERE user_id = ? AND type = 4
        """, (ctx.author.id,))[0][0]

    async def colourFieldMenu(self, ctx, msg, fieldId):

        def check(reaction, user):
            return user.id == ctx.author.id and reaction.emoji in self.WIZARD_EMOJIS.values()

        colour = self.executeSQL("""
            SELECT data FROM fields
            WHERE field_id = ?
        """, (fieldId,))[0][0]

        while True:

            embed = discord.Embed(
                title = "Profile Wizard - Edit a custom colour.",
                description = "React with :zero: to change the image.\nReact with :asterisk: to delete this field.\nReact with :eject: to go back.",
                colour = discord.Colour(int(colour, 16)),
                timestamp = datetime.now(),
            )
            await msg.edit(embed = embed)

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = check)
            except asyncio.TimeoutError:
                return
            await msg.remove_reaction(reaction, user)

            if (reaction.emoji == self.WIZARD_EMOJIS["eject"]):
                return

            elif (reaction.emoji == self.WIZARD_EMOJIS["asterisk"]):
                if (await self.deleteColourField(ctx, msg, fieldId)): return

            elif (reaction.emoji == self.WIZARD_EMOJIS["0"]):
                await self.newColourField(ctx, msg, fieldId)
                colour = self.executeSQL("""
                    SELECT data FROM fields
                    WHERE field_id = ?
                """, (fieldId,))[0][0]

    async def deleteColourField(self, ctx, msg, fieldId):

        def check(msg):
            return ctx.author.id == msg.author.id and ctx.channel.id == msg.channel.id

        embed = discord.Embed(
            title = "Profile Wizard - Delete a custom colour.",
            description = "Are you sure? (Y/N)\n",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        await msg.edit(embed = embed)

        try:
            confirmation = await self.bot.wait_for("message", timeout = 60, check = check)
        except asyncio.TimeoutError:
            return False
        await confirmation.delete()

        if (confirmation.content.lower()[0] != "y"):
            return

        self.executeSQL("""
            DELETE FROM fields
            WHERE field_id = ?
        """, (fieldId,))

        return True

    async def editBio(self, ctx, msg):

        def bio_check(msg):
            return ctx.author.id == msg.author.id and ctx.channel.id == msg.channel.id and len(msg.content) <= 512

        bio = self.executeSQL("""
            SELECT field_id, data FROM fields
            WHERE user_id = ? AND type == 0
        """, (ctx.author.id,))

        embed = discord.Embed(
            title = "Profile Wizard - Edit your bio.",
            description = "Reply with the{} content of the bio. (Max 512 characters)\nWait 300 to cancel.".format(" new" if len(bio) else ""),
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        if (len(bio)):
            embed.add_field(
                name = "Current Bio",
                value = bio[0][1]
            )
        await msg.edit(embed = embed)

        try:
            content = await self.bot.wait_for("message", timeout = 300, check = bio_check)
        except asyncio.TimeoutError:
            return
        await content.delete()
        content = content.content

        if (len(bio)):
            self.executeSQL("""
                UPDATE fields
                SET data = ?
                WHERE field_id = ?
            """, (content, bio[0][0]))

        else:
            self.executeSQL("""
                INSERT INTO fields (user_id, type, name, data)
                VALUES (?, 0, "Bio", ?)
            """, (ctx.author.id, content))

    async def resetProfile(self, ctx, msg):

        def check(msg):
            return ctx.author.id == msg.author.id and ctx.channel.id == msg.channel.id

        embed = discord.Embed(
            title = "Profile Wizard - Reset your profile.",
            description = "Are you sure? (Y/N)\n",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        await msg.edit(embed = embed)

        try:
            confirmation = await self.bot.wait_for("message", timeout = 60, check = check)
        except asyncio.TimeoutError:
            return False
        await confirmation.delete()

        if (confirmation.content.lower()[0] != "y"):
            return

        self.executeSQL("""
            DELETE FROM fields
            WHERE user_id = ?
        """, (ctx.author.id,))

    async def previewProfile(self, ctx, msg):

        def preview_check(reaction, user):
            return ctx.author.id == user.id and msg.id == reaction.message.id and reaction.emoji == self.WIZARD_EMOJIS["eject"]

        await msg.edit(embed = await self.generateProfileEmbed(ctx, ctx.author.id, preview = True))
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = preview_check)
            await msg.remove_reaction(reaction, user)
        except asyncio.TimeoutError:
            pass

    async def generateProfileEmbed(self, ctx, userId, preview = False):

        fields = self.executeSQL("""
            SELECT type, name, data FROM fields
            WHERE user_id = ?
            ORDER BY field_id
        """, (userId,))

        marriages = self.executeSQL("""
            SELECT user_b_id FROM marriages
            WHERE user_a_id = ?
        """, (userId,))

        description = ""
        colour = ctx.guild.get_member(self.bot.user.id).colour
        for field in fields:
            if (field[0] == 0):
                description = field[2]
            elif (field[0] == 4):
                colour = discord.Colour(int(field[2], 16))

        embed = discord.Embed(
            title = "{}'s Profile{}".format((await self.bot.fetch_user(userId)).name, " Preview (React with :eject: to go back)" if preview else "!"),
            description = ":regional_indicator_f: to see friends.\n\n" + description,
            colour = colour,
            timestamp = datetime.now(),
        )

        with open('cogs/profiles.json', 'r') as file:
            d = json.loads(file.read())

        userData = None
        for user in d['users']:
            if user['userid'] == userId:
                userData = user

        embed.add_field(name = "Points", value = "0" if userData == None else userData["points"])
        embed.add_field(name = "Rep", value = "0" if userData == None else userData["rep"])

        if (len(marriages)):
            embed.add_field(name = "Married To", value = "\n".join([(await self.bot.fetch_user(userBID[0])).mention for userBID in marriages]))

        for field in fields:
            if (field[0] == 1 or field[0] == 2):
                embed.add_field(
                    name = field[1],
                    value = field[2],
                    inline = False,
                )
            elif (field[0] == 3):
                embed.set_image(url = field[2])

        return embed

    async def generateFriendsEmbed(self, ctx, userId):
        hasColourField = self.executeSQL("""
            SELECT data FROM fields
            WHERE user_id = ? AND type == 4
        """, (userId,))

        colour = ctx.guild.get_member(self.bot.user.id).colour
        if (len(hasColourField)):
            colour = discord.Colour(int(hasColourField[0][0], 16))

        embed = discord.Embed(
            title = "{}'s Friends!".format((await self.bot.fetch_user(userId)).name),
            description = ":regional_indicator_f: to go back to the profile.",
            colour = colour,
            timestamp = datetime.now(),
        )

        relationships = self.executeSQL("""
            SELECT user_b_id, type FROM relationships
            WHERE user_a_id = ?
            ORDER BY relationship_id
        """, (userId,))

        f = ""
        bf = ""
        for relationship in relationships:
            if (relationship[1] == 0):
                f += (await self.bot.fetch_user(relationship[0])).mention + "\n"
            elif (relationship[1] == 1):
                bf += (await self.bot.fetch_user(relationship[0])).mention + "\n"

        embed.add_field(name = "Best Friends", value = bf if bf else "None", inline = False)
        embed.add_field(name = "Friends", value = f if f else "None", inline = False)

        return embed

    @commands.command(
        name = "testprofile",

        usage = "@User",

        brief = "View someone's profile!",
        description = "View all about a user!",
    )
    async def profile(self, ctx):

        if (len(ctx.message.mentions) == 0):
            userId = ctx.author.id
        else:
            userId = ctx.message.mentions[0].id

        embed = discord.Embed(
            title = "Profile Wizard",
            description = "Loading...",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        msg = await ctx.send(embed = embed)
        await msg.add_reaction("🇫")

        def check(reaction, user):
            return ctx.author.id == user.id and msg.id == reaction.message.id and reaction.emoji == "🇫"

        while True:

            await msg.edit(embed = await self.generateProfileEmbed(ctx, userId))

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 300, check = check)
            except asyncio.TimeoutError:
                return
            await msg.remove_reaction(reaction, user)

            await msg.edit(embed = await self.generateFriendsEmbed(ctx, userId))

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = check)
            except asyncio.TimeoutError:
                return
            await msg.remove_reaction(reaction, user)

    @commands.command(
        name = "friend",

        brief = "Friend another user!",
        description = "Friend someone! (Use it again to best friend them!)",
    )
    async def friend(self, ctx):

        def check(msg):
            return member.id == msg.author.id and ctx.channel.id == msg.channel.id

        for member in ctx.message.mentions:

            if (ctx.author.id == member.id):
                await ctx.send("You can't friend yourself!")
                continue

            relationship = self.executeSQL("""
                SELECT relationship_id, type FROM relationships
                WHERE user_a_id = ? AND user_b_id = ?
            """, (ctx.author.id, member.id))

            if (len(relationship) and relationship[0][1] == 0):

                if (self.executeSQL("""
                    SELECT COUNT(*) FROM relationships
                    WHERE user_a_id = ? AND type = 1
                """, (ctx.author.id,))[0][0] >= 5):
                    await ctx.send("You can't have more than 5 best friends!")

                elif (self.executeSQL("""
                    SELECT COUNT(*) FROM relationships
                    WHERE user_b_id = ? AND type = 1
                """, (member.id,))[0][0] >= 5):
                    await ctx.send("They already have 5 best friends!")

                else:
                    msg = await ctx.send("{} do you want to be best friends with {}? (Y/N)".format(member.mention, ctx.author.mention))

                    try:
                        accept = await self.bot.wait_for("message", timeout = 60, check = check)
                    except asyncio.TimeoutError:
                        await msg.edit(content = "I guess {} didn't want to be best friends with you. <:sadplant:828679930450673714>".format(member.mention))
                        continue

                    if (accept.content.lower()[0] == "y"):
                        self.executeSQL("""
                            UPDATE relationships
                            SET type = 1
                            WHERE relationship_id = ?
                        """, (relationship[0][0],))

                        relationship2 = self.executeSQL("""
                            SELECT relationship_id FROM relationships
                            WHERE user_a_id = ? AND user_b_id = ?
                        """, (member.id, ctx.author.id))

                        if (len(relationship2)):
                            self.executeSQL("""
                                UPDATE relationships
                                SET type = 1
                                WHERE relationship_id = ?
                            """, (relationship2[0][0],))

                        else:
                            self.executeSQL("""
                                INSERT INTO relationships (user_a_id, user_b_id, type)
                                VALUES (?, ?, 1)
                            """, (member.id, ctx.author.id))

                        await msg.edit(content = "{} and {} are now best friends! <:plantlove:829795421369925681>".format(ctx.author.mention, member.mention))

                    else:
                        await msg.edit(content = "{} didn't want to be best friends with you. <:sadplant:828679930450673714>".format(member.mention))


            elif (len(relationship) and relationship[0][1] == 1):
                await ctx.send(content = "You are already best friends with {}! <:plantlove:829795421369925681>".format(member.mention))

            elif (not len(relationship)):
                self.executeSQL("""
                    INSERT INTO relationships (user_a_id, user_b_id, type)
                    VALUES (?, ?, 0)
                """, (ctx.author.id, member.id))

                await ctx.send("You are now friends with {}! <:plantlove:829795421369925681>".format(member.mention))

    @commands.command(
        name = "unfriend",

        brief = "Unfriend another user.",
        description = "Unfriend someone!",
    )
    async def unfriend(self, ctx):

        for member in ctx.message.mentions:

            if (ctx.author.id == member.id):
                await ctx.send("You can't unfriend yourself!")
                continue

            relationship = self.executeSQL("""
                SELECT relationship_id, type FROM relationships
                WHERE user_a_id = ? AND user_b_id = ?
            """, (ctx.author.id, member.id))

            if (len(relationship) and relationship[0][1] == 1):
                relationship2 = self.executeSQL("""
                    SELECT relationship_id FROM relationships
                    WHERE user_a_id = ? AND user_b_id = ?
                """, (member.id, ctx.author.id))

                self.executeSQL("""
                    UPDATE relationships
                    SET type = 0
                    WHERE relationship_id = ? OR relationship_id = ?
                """, (relationship[0][0], relationship2[0][0]))

                await ctx.send("{} and {} are now only friends. <:sadplant:828679930450673714>".format(ctx.author.mention, member.mention))

            elif (len(relationship) and relationship[0][1] == 0):
                self.executeSQL("""
                    DELETE FROM relationships
                    WHERE relationship_id = ?
                """, (relationship[0][0],))

                await ctx.send("You are no longer friends with {}. <:sadplant:828679930450673714>".format(member.mention))

            else:
                await ctx.send("You don't have a friendship with {}. <:sadplant:828679930450673714>".format(member.mention))

    @commands.command(
        name = "testmarry",

        brief = "Marry another user!",
        description = "Marry someone!",
    )
    async def marry(self, ctx):

        def check(msg):
            return member.id == msg.author.id and ctx.channel.id == msg.channel.id

        for member in ctx.message.mentions:

            if (ctx.author.id == member.id):
                await ctx.send("You can't marry yourself!")
                continue

            marriage = self.executeSQL("""
                SELECT marriage_id FROM marriages
                WHERE user_a_id = ? AND user_b_id = ?
            """, (ctx.author.id, member.id))

            if (not len(marriage)):

                if (self.executeSQL("""
                    SELECT COUNT(*) FROM marriages
                    WHERE user_a_id = ?
                """, (ctx.author.id,))[0][0] >= 3):
                    await ctx.send("You can't have more than 3 marriages!")

                elif (self.executeSQL("""
                    SELECT COUNT(*) FROM marriages
                    WHERE user_b_id = ?
                """, (member.id,))[0][0] >= 3):
                    await ctx.send("They already have 3 marriages!")

                else:
                    msg = await ctx.send("{} do you want to marry {}? (Y/N)".format(member.mention, ctx.author.mention))

                    try:
                        accept = await self.bot.wait_for("message", timeout = 60, check = check)
                    except asyncio.TimeoutError:
                        await msg.edit(content = "I guess {} didn't want to marry you. <:sadplant:828679930450673714>".format(member.mention))
                        continue

                    if (accept.content.lower()[0] == "y"):

                        self.executeSQL("""
                            INSERT INTO relationships (user_a_id, user_b_id, type)
                            VALUES (?, ?, 1)
                        """, (ctx.author.id, member.id))

                        self.executeSQL("""
                            INSERT INTO relationships (user_a_id, user_b_id, type)
                            VALUES (?, ?, 1)
                        """, (member.id, ctx.author.id))

                        await msg.edit(content = "{} and {} are now married! <:plantlove:829795421369925681>".format(ctx.author.mention, member.mention))

                    else:
                        await msg.edit(content = "{} didn't want to marry you. <:sadplant:828679930450673714>".format(member.mention))

            else:
                await ctx.send("You are already married to {}! <:plantlove:829795421369925681>".format(member.mention))

    @commands.command(
        name = "testdivorce",

        brief = "Divorce another user.",
        description = "Divorce someone!",
    )
    async def divorce(self, ctx):

        for member in ctx.message.mentions:

            if (ctx.author.id == member.id):
                await ctx.send("You can't divorce yourself!")
                continue

            relationship = self.executeSQL("""
                SELECT marriage_id FROM marriages
                WHERE user_a_id = ? AND user_b_id = ?
            """, (ctx.author.id, member.id))

            if (len(relationship)):

                self.executeSQL("""
                    DELETE FROM marriages 
                    WHERE user_a_id = ? AND user_b_id = ?
                """, (ctx.author.id, member.id))

                self.executeSQL("""
                    DELETE FROM marriages 
                    WHERE user_a_id = ? AND user_b_id = ?
                """, (member.id, ctx.author.id))

                await ctx.send("{} and {} are no longer married. <:sadplant:828679930450673714>".format(ctx.author.mention, member.mention))

            else:
                await ctx.send("You aren't married to {}. <:sadplant:828679930450673714>".format(member.mention))

def setup(bot):
    bot.add_cog(Profile(bot))
