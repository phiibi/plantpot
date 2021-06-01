#helpers.py

import discord
import time

from discord.ext import tasks
from aiosqlite import connect
from cogs.event import Event
from cogs.inventory import Inventory
from cogs.leaderboard import Leaderboard

class EventChecker:

    def __init__(self, bot):
        self.bot = bot
        self.setup.start()

    async def executesql(self, statement, data=()):
        db = await connect('database.db')
        cursor = await db.execute(statement, data)
        await db.commit()
        rows = await cursor.fetchall()
        await cursor.close()
        await db.close()
        return list(rows)

    @tasks.loop(count=1)
    async def setup(self):
        await self.executesql("PRAGMA foreign_keys = ON")
        await self.executesql("""CREATE TABLE IF NOT EXISTS cooldowns (
                    active_id PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    last_pickup FLOAT NOT NULL,
                    CONSTRAINT fk_active FOREIGN KEY (active_id) REFERENCES active_events(active_id))""")

    @setup.before_loop
    async def before_setup(self):
        await self.bot.wait_until_ready()

    async def eventcollect(self, payload):
        activeinfo = await self.executesql('SELECT active_id, event_id, image_id FROM active_posts WHERE message_id = ?', (payload.message_id,))
        if not len(activeinfo):
            return

        await self.executesql('UPDATE active_posts SET message_id = ? WHERE active_id = ?', (0, activeinfo[0][0]))
        imageinfo = await self.executesql('SELECT r.rarity_name, r.points_first, r.points_second FROM rarities r INNER JOIN images i USING (rarity_id) WHERE i.image_id = ?', (activeinfo[0][2],))
        previouspickup = await self.executesql('SELECT count FROM inventories WHERE (user_id = ? AND server_id = ? AND image_id = ?)', (payload.user_id, payload.guild_id, activeinfo[0][2]))
        cd = await self.executesql('SELECT last_pickup FROM cooldowns WHERE (active_id = ? AND user_id = ?)', (activeinfo[0][0], payload.user_id))

        if cd[0][0] - 150 < time.time():
            return await self.bot.get_guild(payload.guild_id).get_channel(payload.channel_id).send(f"hold up {payload.member.mention}, you've collected an item too recently, please wait a second to give other users a chance!")

        pickupstring = 'a'
        if imageinfo[0][0][:1] in ['a', 'e', 'i', 'o', 'u']:
            pickupstring += 'n'

        await self.bot.get_guild(payload.guild_id).get_channel(payload.channel_id).send(f'**{payload.member.mention}, you just picked up {pickupstring} {imageinfo[0][0]} item!**')

        if len(previouspickup) and imageinfo[0][0] != 'common':
            await self.bot.get_guild(payload.guild_id).get_channel(payload.channel_id).send(f'**as you\'ve collected this before, you\'ve earned {imageinfo[0][2]} points!**')
            await Leaderboard.addpoints(self, payload.user_id, payload.guild_id, activeinfo[0][1], imageinfo[0][2])
        else:
            await self.bot.get_guild(payload.guild_id).get_channel(payload.channel_id).send(f'**you\'ve earned {imageinfo[0][1]} points!**')
            await Leaderboard.addpoints(self, payload.user_id, payload.guild_id, activeinfo[0][1], imageinfo[0][1])

        await Inventory.additem(self, payload.user_id, payload.guild_id, activeinfo[0][1], activeinfo[0][2], 1)
        await self.executesql('REPLACE INTO cooldowns (user_id, last_pickup) VALUES (?, ?)' (payload.user_id, time.time()))
        await Event.eventpost(self, activeinfo[0][0])

class ReactionChecker:
    def __init__(self, bot):
        self.bot = bot
        self.setup.start()

    async def executesql(self, statement, data=()):
        db = await connect('database.db')
        cursor = await db.execute(statement, data)
        await db.commit()
        rows = await cursor.fetchall()
        await cursor.close()
        await db.close()
        return list(rows)

    @tasks.loop(count=1)
    async def setup(self):
        await self.executesql("PRAGMA foreign_keys = ON")

    @setup.before_loop
    async def before_setup(self):
        await self.bot.wait_until_ready()

    async def addreactions(self, payload):
        manager = await self.executesql('SELECT manager_id FROM activemanagers WHERE (message_id = ? AND channel_id = ?)', (payload.message_id, payload.channel_id))
        if not len(manager):
            return
        rolelist = await self.executesql('SELECT role_id, emoji FROM roles WHERE manager_id = ?', (manager[0][0],))
        role = [role for role in rolelist if str(role[1]) == str(payload.emoji)]
        if len(role[0]):
            role = self.bot.get_guild(payload.guild_id).get_role(role[0][0])
            try:
                if role not in payload.member.roles:
                    await payload.member.add_roles(role)
                elif role in payload.member.roles:
                    await payload.member.remove_roles(role)
            except discord.errors.Forbidden:
                await self.bot.get_channel(payload.channel_id).send('I cannot assign you this role as either it is higher than me in the hierarchy or I do not have `manage roles` permissions')
