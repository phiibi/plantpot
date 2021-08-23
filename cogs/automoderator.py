import discord
from discord.ext import commands, tasks
from aiosqlite import connect
import asyncio


class AutoModerator(commands.Cog):

    version = '1.0'

    EMOJIS = {
        "A":              "🇦",
        "B":              "🇧",
        "eject":          "⏏️",
    }

    def __init__(self, bot):
        self.bot = bot

        self.setup.start()

    @tasks.loop(count=1)
    async def setup(self):
        await self.executesql("PRAGMA foreign_keys = ON")

        await self.executesql("""
            CREATE TABLE IF NOT EXISTS welcome_messages (
                id INTEGER PRIMARY KEY,
                server_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message TEXT NOT NULL
            )
        """)

        await self.executesql("""
            CREATE TABLE IF NOT EXISTS welcome_role (
                wr_id INTEGER PRIMARY KEY,
                server_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
            )
        """)


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

    async def autoModCheck(ctx):
        return ctx.author.permissions_in(ctx.channel).manage_guild or 825241813505802270 in [role.id for role in ctx.author.roles]

    @commands.group(name='automod', hidden=True, help='use .badge help for more help!')
    async def automod(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    async def automodmenu(self, ctx):
        def check(r, u):
            return u == ctx.author and r.message == m

        embed = discord.Embed(title='Automoderator Menu',
                              description='Loading...',
                              colour=ctx.guild.get_member(self.bot.user.id).colour)
        m = await ctx.send(embed=embed)

        for e in self.EMOJIS.values():
            await m.add_reaction(e)



        while True:
            embed.description = "*Please react to choose an auto moderation tool*\n🇦 Welcome message \n🇧 Auto role assignment\nWait 60s, or react :eject: to quit"
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

    @automod.command(name='welcome', aliases=['wm', 'message'])
    async def welcomemessage(self, ctx, m=None):
        def check(r, u):
            return u == ctx.author and r.message == m

        messageinfo = await self.executesql('SELECT id, channel_id, message FROM welcome_messages WHERE server_id = ?', (ctx.guild.id,))

        if messageinfo[0]:
            embed = discord.Embed(title='Auto Moderation Menu',
                                  description='React to edit welcome\nReact 🇦 to change message\nReact with 🇧 to change the channel\nReact :asterisk: to delete\nWait 60s, or react :eject: to go back',
                                  colour=ctx.guild.get_member(self.bot.user.id).colour)
            embed.add_field(name='Message',
                            value=messageinfo[0][2],
                            inline=False)
            embed.add_field(name='Channel',
                            value=f'Welcome messages posting in {self.bot.get_channel(messageinfo[0][1]).mention}',
                            inline=False)

    async def updatemessage(self, ctx, m):
        def check(msg):
            return msg.author == ctx.author and msg.channel == m.channel

        embed = discord.Embed(title='Welcome Message',
                              description='Please send the welcome message you would like me to send.\nWait 60s, or reply `exit` to exit')
