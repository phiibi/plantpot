import discord
from discord.ext import commands, tasks
from aiosqlite import connect
import asyncio


class RoleManager(commands.Cog):

    version = '1.2'

    EMOJIS = {
        "0":              "0️⃣",
        "1":              "1️⃣",
        "2":              "2️⃣",
        "3":              "3️⃣",
        "4":              "4️⃣",
        "5":              "5️⃣",
        "6":              "6️⃣",
        "7":              "7️⃣",
        "8":              "8️⃣",
        "9":              "9️⃣",
        "left_arrow":     "⬅️",
        "right_arrow":    "➡️",
        "new":            "🆕",
        "record_button":  "⏺️",
        "asterisk":       "*️⃣",
        "eject":          "⏏️",
    }

    def __init__(self, bot):
        self.bot = bot

        self.setup.start()

    @tasks.loop(count=1)
    async def setup(self):
        await self.executesql("PRAGMA foreign_keys = ON")

        await self.executesql("""
            CREATE TABLE IF NOT EXISTS rolemanagers (
                manager_id INTEGER PRIMARY KEY,
                server_id INTEGER NOT NULL,
                title TEXT NOT NULL
            )
        """)
        await self.executesql("""
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY,
                manager_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                emoji TEXT NOT NULL,
                CONSTRAINT fk_manager FOREIGN KEY (manager_id) REFERENCES rolemanagers(manager_id) ON DELETE CASCADE
            )
        """)
        await self.executesql("""
        CREATE TABLE IF NOT EXISTS activemanagers (
            active_id INTEGER PRIMARY KEY,
            manager_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            CONSTRAINT fk_manager FOREIGN KEY (manager_id) REFERENCES rolemanagers(manager_id) ON DELETE CASCADE)""")

    @setup.before_loop
    async def before_setup(self):
        await self.bot.wait_until_ready()

    async def executesql(self, statement, data=()):
        db = await connect('database.db')
        cursor = await db.execute(statement, data)
        await db.commit()
        rows = await cursor.fetchall()
        await cursor.close()
        await db.close()
        return list(rows)

    async def roleManagerCheck(ctx):
        return ctx.author.permissions_in(ctx.channel).manage_guild or 825241813505802270 in [role.id for role in ctx.author.roles]

#
#
# ------------------- MENUS ------------------- #
#
#

    @commands.command(name='rolemanager', help='create a new role manager', aliases=['rm'])
    @commands.check(roleManagerCheck)
    async def rolemanager(self, ctx):
        embed = discord.Embed(title='Role Manager Menu',
                              description='Loading...',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        m = await ctx.send(embed=embed)

        for e in self.EMOJIS.values():
            await m.add_reaction(e)

        p = await self.rolemanagermainmenu(ctx, m)

        if p:
            #if rolemanager goes all the way through to a post, don't try to do more
            return

        await m.clear_reactions()

        embed.description = 'Finished'
        await m.edit(embed=embed)

    async def rolemanagermainmenu(self, ctx, m):
        def check(r, u):
            return u == ctx.author and r.message == m

        await self.unloadactives(ctx)

        rolemanagerlist = await self.executesql('SELECT manager_id, title FROM rolemanagers WHERE server_id = ?', (ctx.guild.id,))
        page = 0

        while True:
            embed = discord.Embed(title='Select a Role Manager',
                                  description='React a number to select a role manager\nReact :arrow_left: to go backwards a page\nReact :arrow_right: to go forward a page\nReact :new: to create a new role manager\nReact :record_button: to post a role manager\nReact :eject: to quit',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)
            if len(rolemanagerlist):
                embed.add_field(name=f'Available Role Managers ({page * 10 + 1}-{min(page * 10 + 10, len(rolemanagerlist))}/{len(rolemanagerlist)})',
                                value="\n".join(f'{self.EMOJIS[str(i)]} {rolemanagerlist[page*10 + i][1]}' for i in range(0, len(rolemanagerlist[page*10:page*10+10]))))
            else:
                embed.add_field(name='Your Role Managers (0/0)',
                                value='None')
            await m.edit(embed=embed)

            try:
                r, u = await self.bot.wait_for("reaction_add", check=check, timeout=60)
            except asyncio.TimeoutError:
                return

            try:
                await m.remove_reaction(r, u)
            except discord.errors.Forbidden:
                await ctx.send('I cannot continue as I need `manage message` permissions for this menu, please enable them and try again!')
                return

            if r.emoji == self.EMOJIS['left_arrow']:
                page -= 1
                page %= ((len(rolemanagerlist) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS['right_arrow']:
                page += 1
                page %= ((len(rolemanagerlist) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS['new']:
                await self.newrolemanager(ctx, m)
                rolemanagerlist = await self.executesql('SELECT manager_id, title FROM rolemanagers WHERE server_id = ?', (ctx.guild.id,))
                page = 0
            elif r.emoji == self.EMOJIS['asterisk']:
                pass
            elif r.emoji == self.EMOJIS['record_button']:
                p = await self.postmenu(ctx, m)
                if p:
                    return p
            elif r.emoji == self.EMOJIS['eject']:
                return
            elif r.emoji in self.EMOJIS.values():
                if page*10 + int(r.emoji[0]) < len(rolemanagerlist):
                    await self.managermenu(ctx, m, rolemanagerlist[page*10 + int(r.emoji[0])][0])
                    rolemanagerlist = await self.executesql('SELECT manager_id, title FROM rolemanagers WHERE server_id = ?', (ctx.guild.id,))
                    page = 0

    async def managermenu(self, ctx, m, managerid):
        def check(r, u):
            return u == ctx.author and r.message == m

        manager = await self.executesql('SELECT title FROM rolemanagers WHERE manager_id = ?', (managerid,))
        manager = manager[0][0]
        rolelist = await self.executesql('SELECT id, role_id FROM roles WHERE manager_id = ?', (managerid,))
        activity = await self.executesql('SELECT channel_id FROM activemanagers WHERE manager_id = ?', (managerid,))
        page = 0

        while True:

            embed = discord.Embed(title=f'{manager} - Select a Role',
                                  description="React a number to select that role\nReact :arrow_left: to go back a page\nReact :arrow_right: to go forward a page\nReact :new: to add a new role\nReact :record_button: to change the role manager title\nReact :asterisk: to delete the role manager\nReact :eject: to go back",
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)
            if len(activity):
                embed.add_field(name='ACTIVE',
                                value=f'This manager is currently active in {self.bot.get_channel(activity[0][0]).mention}',
                                inline=False)
            if len(rolelist):
                embed.add_field(name=f'Available Roles ({page * 10 + 1}-{min(page * 10 + 10, len(rolelist))}/{len(rolelist)})',
                                value="\n".join(f'{self.EMOJIS[str(i)]} {ctx.guild.get_role(rolelist[page*10 + i][1]).name}' for i in range(0, len(rolelist[page*10:page*10+10]))))
            else:
                embed.add_field(name='Available Roles', value='None')
            await m.edit(embed=embed)

            try:
                r, u = await self.bot.wait_for("reaction_add", check=check, timeout=60)
            except asyncio.TimeoutError:
                return
            await m.remove_reaction(r, u)

            if r.emoji == self.EMOJIS["left_arrow"]:
                page -= 1
                page %= ((len(rolelist) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS["right_arrow"]:
                page += 1
                page %= ((len(rolelist) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS["new"]:
                role = await self.newrole(ctx, m, managerid)
                await self.updateactive(ctx, managerid)
                rolelist = await self.executesql('SELECT id, role_id FROM roles WHERE manager_id = ?', (managerid,))
                page = 0
            elif r.emoji == self.EMOJIS["record_button"]:
                title = await self.makename(ctx, m)
                if title:
                    await self.updateactive(ctx, managerid)
                    await self.executesql('UPDATE rolemanagers SET title = ? WHERE manager_id = ?', (title, managerid))
                    manager = await self.executesql('SELECT title FROM rolemanagers WHERE manager_id = ?', (managerid,))
                    manager = manager[0][0]
            elif r.emoji == self.EMOJIS['asterisk']:
                await self.deletemanager(ctx, m, managerid)
                return
            elif r.emoji == self.EMOJIS["eject"]:
                return
            elif r.emoji in self.EMOJIS.values():
                if page*10 + int(r.emoji[0]) < len(rolelist):
                    await self.rolemenu(ctx, m, managerid, rolelist[page*10 + int(r.emoji[0])][0])
                    rolelist = await self.executesql('SELECT id, role_id FROM roles WHERE manager_id = ?', (managerid,))
                    page = 0

    async def rolemenu(self, ctx, m, managerid, roleid):
        def check(r, u):
            return u == ctx.author and r.message == m

        role = await self.executesql('SELECT id, role_id, emoji FROM roles WHERE (manager_id = ? AND id = ?)', (managerid, roleid))

        while True:
            embed = discord.Embed(title=f'Role Manager Menu - {ctx.guild.get_role(role[0][1]).name}',
                                  description='React :zero: to change the role\nReact :one: to change the emoji\nReact :asterisk: to delete the reaction\nReact :eject: to go back',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)
            if await self.checkrole(ctx, role[0][1]):
                embed.add_field(name='ROLE UNASSIGNABLE', value='This role is higher in the hierarchy than me so I cannot assign it to other users', inline=False)
            embed.add_field(name='Role', value=ctx.guild.get_role(role[0][1]).name)
            embed.add_field(name='Emoji', value=role[0][2])

            await m.edit(embed=embed)

            try:
                r, u = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            except asyncio.TimeoutError:
                return

            await m.remove_reaction(r, u)

            if r.emoji == self.EMOJIS['0']:
                newrole = await self.makerole(ctx, m, managerid)
                if newrole:
                    await self.executesql('UPDATE roles SET role_id = ? WHERE id = ?', (newrole, roleid))
                    await self.updateactive(ctx, managerid)
                    role = await self.executesql('SELECT id, role_id, emoji FROM roles WHERE id = ?', (roleid,))
            elif r.emoji == self.EMOJIS['1']:
                newemoji = await self.make_emoji(ctx, m, managerid)
                if newemoji:
                    await self.executesql('UPDATE roles SET emoji = ? WHERE id = ?', (newemoji, roleid))
                    await self.updateactive(ctx, managerid)
                    role = await self.executesql('SELECT id, role_id, emoji FROM roles WHERE id = ?', (roleid,))
            elif r.emoji == self.EMOJIS['asterisk']:
                await self.deleterole(ctx, m, roleid)
                return
            elif r.emoji == self.EMOJIS['eject']:
                return

    async def postmenu(self, ctx, m):
        def check(r, u):
            return u == ctx.author and r.message == m

        rolemanagerlist = await self.executesql("""SELECT rolemanagers.manager_id, rolemanagers.title FROM rolemanagers 
                                             LEFT JOIN activemanagers USING (manager_id)
                                             WHERE (rolemanagers.server_id = ? AND activemanagers.manager_id IS NULL)""", (ctx.guild.id,))
        page = 0

        while True:
            embed = discord.Embed(title='Post a New Role Manager',
                                  description='React a number to select a role manager to post\nReact :arrow_left: to go backwards a page\nReact :arrow_right: to go forward a page\nReact :eject: to go back',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)
            if len(rolemanagerlist):
                embed.add_field(name=f'Available Role Managers ({page * 10 + 1}-{min(page * 10 + 10, len(rolemanagerlist))}/{len(rolemanagerlist)})',
                                value="\n".join(f'{self.EMOJIS[str(i)]} {rolemanagerlist[page*10 + i][1]}' for i in range(0, len(rolemanagerlist[page*10:page*10+10]))))
            else:
                embed.add_field(name='Your Role Managers (0/0)',
                                value='None')
            await m.edit(embed=embed)

            try:
                r, u = await self.bot.wait_for("reaction_add", check=check, timeout=60)
            except asyncio.TimeoutError:
                return

            await m.remove_reaction(r, u)

            if r.emoji == self.EMOJIS['left_arrow']:
                page -= 1
                page %= ((len(rolemanagerlist) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS['right_arrow']:
                page += 1
                page %= ((len(rolemanagerlist) - 1) // 10 + 1)
            elif r.emoji == self.EMOJIS['new']:
                return
            elif r.emoji == self.EMOJIS['asterisk']:
                return
            elif r.emoji == self.EMOJIS['record_button']:
                return
            elif r.emoji == self.EMOJIS['eject']:
                return
            elif r.emoji in self.EMOJIS.values():
                if page*10 + int(r.emoji[0]) < len(rolemanagerlist):
                    return await self.convertmenu(ctx, m, rolemanagerlist[page*10 + int(r.emoji[0])][0])

    async def convertmenu(self, ctx, m, managerid):
        manager = await self.executesql('SELECT title FROM rolemanagers WHERE manager_id = ?', (managerid,))
        rolelist = await self.executesql('SELECT role_id, emoji FROM roles WHERE manager_id = ?', (managerid,))

        await m.clear_reactions()

        embed = discord.Embed(title=f'{manager[0][0]}',
                              description='Loading...',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)

        await m.edit(embed=embed)

        for role in rolelist:
            try:
                await m.add_reaction(role[1])
            except discord.errors.NotFound:
                pass

        embed.description = 'Please react to add roles\n' + '\n'.join(f'{role[1]} {ctx.guild.get_role(role[0]).mention}' for role in rolelist)
        embed.set_footer(text='Powered by chlorophyll')

        await self.executesql('INSERT INTO activemanagers (manager_id, channel_id, message_id) VALUES (?, ?, ?)', (managerid, ctx.channel.id, m.id))

        await m.edit(embed=embed)

        return True

    async def updateactive(self, ctx, managerid):
        active = await self.executesql('SELECT message_id, channel_id FROM activemanagers WHERE manager_id = ?', (managerid,))
        if not len(active):
            return
        try:
            m = await self.bot.get_channel(active[0][1]).fetch_message(active[0][0])
        except discord.errors.NotFound:
            return
        await self.convertmenu(ctx, m, managerid)

#
#
# ------------------- SETTERS ------------------- #
#
#

    async def newrolemanager(self, ctx, m):
        def check(r, u):
            return u == ctx.author and r.emoji == self.EMOJIS["eject"]

        if (not len(await self.executesql("""SELECT server_id 
                                       FROM premium_users 
                                       WHERE server_id = ?""", (ctx.guild.id,))) and len(await self.executesql("""SELECT manager_id 
                                                                                                            FROM rolemanagers 
                                                                                                            WHERE server_id = ?""", (ctx.guild.id,))) >= 3):
            embed = discord.Embed(title='Role Manager - New Manager',
                                  description='You need to purchase premium to have more than 3 role managers per server!\nReact :eject: or wait 60s to go back',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)
            await m.edit(embed=embed)
            try:
                r, u = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            except asyncio.TimeoutError:
                return
            await m.remove_reaction(r, u)
            return

        title = await self.makename(ctx, m)

        await self.executesql('INSERT INTO rolemanagers (server_id, title) VALUES (?, ?)', (ctx.guild.id, title))

        managerid = await self.executesql('SELECT manager_id FROM rolemanagers WHERE (server_id = ? AND title = ?)', (ctx.guild.id, title))

        await self.managermenu(ctx, m, managerid[0][0])

    async def newrole(self, ctx, m, managerid):

        roleid = await self.makerole(ctx, m, managerid)

        if not roleid:
            return

        emoji = await self.make_emoji(ctx, m, managerid)

        if not emoji:
            return

        await self.executesql('INSERT INTO roles (manager_id, role_id, emoji) VALUES (?, ?, ?)', (managerid, roleid, emoji))

    async def makename(self, ctx, m):
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        embed = discord.Embed(title='Name Your Role Manager',
                              description='Please reply with the title of your role manager\nWait 60s to cancel',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        await m.edit(embed=embed)

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=60)
        except asyncio.TimeoutError:
            return

        await msg.delete()

        return msg.content

    async def makerole(self, ctx, m, managerid):
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        addedroles = [role[0] for role in await self.executesql('SELECT role_id FROM roles WHERE manager_id = ?', (managerid,))]

        embed = discord.Embed(title='Role Manager Menu - Role',
                              description='Please mention the new role\n**Please make sure my roles are higher than this role otherwise I cannot assign it users**\nWait 60s to go back',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        await m.edit(embed=embed)

        while True:
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=60)
            except asyncio.TimeoutError:
                return

            await msg.delete()

            if not len(msg.role_mentions):
                embed.description = 'Please @ mention the new role\nWait 60s to go back'
                await m.edit(embed=embed)
            elif len(msg.role_mentions) > 1:
                embed.description = 'Please only mention one role\nWait 60s to go back'
                await m.edit(embed=embed)
            elif msg.role_mentions[0].id in addedroles:
                embed.description = 'This role is already added, please mention a new role\nWait 60s to go back'
                await m.edit(embed=embed)
            else:
                return msg.role_mentions[0].id

    async def make_emoji(self, ctx, m, managerid):
        def check(r, u):
            return u == ctx.author and r.message == m

        usedemojis = [emoji[0] for emoji in await self.executesql('SELECT emoji FROM roles WHERE manager_id = ?', (managerid,))]
        premium = len(await self.executesql("""SELECT server_id FROM premium_users WHERE server_id = ?""", (ctx.guild.id,)))

        descstring = 'Please react the emoji you would like to add\n'
        if premium:
            descstring += '**Please don\'t use emojis from other servers as I cannot use them!**\n'
        descstring += 'Wait 60s to go back'

        embed = discord.Embed(title='Role Manager Menu - Emoji',
                              description=descstring,
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        await m.edit(embed=embed)

        while True:
            try:
                r, u = await self.bot.wait_for("reaction_add", check=check, timeout=60)
            except asyncio.TimeoutError:
                return
            await m.remove_reaction(r, u)

            if type(r.emoji) == discord.PartialEmoji:
                if premium:
                    embed.description = 'Please only use emojis from this server!\nPlease react a new emoji, or wait 60s to go back'
                else:
                    embed.description = 'You need to purchase premium to use custom emojis!\nPlease react a new emoji, or wait 60s to go back'
                await m.edit(embed=embed)
            elif type(r.emoji) == discord.Emoji and not premium:
                embed.description = 'You need to purchase premium to use custom emojis!\nPlease react a new emoji, or wait 60s to go back'
                await m.edit(embed=embed)
            elif str(r.emoji) in usedemojis:
                embed.description = 'You are already using this emoji!\nPlease react a new emoji, or wait 60s to go back'
                await m.edit(embed=embed)
            else:
                return str(r.emoji)
#
#
# ------------------- DELETE ------------------- #
#
#
    async def deletemanager(self, ctx, m, managerid):
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        embed = discord.Embed(title='Delete Role Manager?',
                              description='Are you sure you would like to delete this role manager? [(y)es/(n)o]',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        await m.edit(embed=embed)

        while True:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                return

            await msg.delete()

            if msg.content.lower() in ['y', 'yes']:
                await self.deleteactive(ctx, managerid)
                await self.executesql('DELETE FROM rolemanagers WHERE manager_id = ?', (managerid,))
                return
            elif msg.content.lower() in ['n', 'no']:
                return
            else:
                embed.description = 'I could\'t understand that, would you like to delete this role? [(y)es/(n)o]'
                await m.edit(embed=embed)

    async def deleterole(self, ctx, m, roleid):
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        embed = discord.Embed(title='Delete Role?',
                              description='Are you sure you would like to delete this role? [(y)es/(n)o]',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        await m.edit(embed=embed)

        while True:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                return

            await msg.delete()

            if msg.content.lower() in ['y', 'yes']:
                await self.executesql('DELETE FROM roles WHERE id = ?', (roleid,))
                return
            elif msg.content.lower() in ['n', 'no']:
                return
            else:
                embed.description = 'I could\'t understand that, would you like to delete this role? [(y)es/(n)o]'
                await m.edit(embed=embed)

    async def deleteactive(self, ctx, managerid):
        active = await self.executesql('SELECT message_id, channel_id FROM activemanagers WHERE manager_id = ?', (managerid,))
        if not len(active):
            return
        try:
            m = await self.bot.get_channel(active[0][1]).fetch_message(active[0][0])
            await m.delete()
            await ctx.send(f'Deleting active manager from {self.bot.get_channel(active[0][1]).mention}')
        except discord.errors.NotFound:
            return

    #deletes active manager entries from db if the post has been deleted
    async def unloadactives(self, ctx):
        activemanagerlist = await self.executesql("""SELECT active_id, message_id, channel_id FROM activemanagers 
                                               INNER JOIN rolemanagers USING(manager_id) 
                                               WHERE rolemanagers.server_id = ?""", (ctx.guild.id,))
        for manager in activemanagerlist:
            try:
                await self.bot.get_channel(manager[2]).fetch_message(manager[1])
            except discord.errors.NotFound:
                await self.executesql('DELETE FROM activemanagers WHERE active_id = ?', (manager[0],))

#
#
# ------------------- OTHER FUNCTIONS ------------------- #
#
#

    async def checkrole(self, ctx, roleid):
        guildroleidlist = [r.id for r in ctx.guild.roles]

        return guildroleidlist.index(roleid) > guildroleidlist.index([r.id for r in ctx.guild.get_member(self.bot.user.id).roles][-1])


def setup(bot):
    bot.add_cog(RoleManager(bot))
