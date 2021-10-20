#helpers.py

import discord
import random
import time

from discord.ext import tasks
from aiosqlite import connect
from cogs.event import Event
from cogs.inventory import Inventory
from cogs.leaderboard import Leaderboard

class EventChecker:
    SPOOKY_REPLIES = ["It's a boo-tiful day to get points!",
                      "Your ancestors saw that, they're proud of you...",
                      "You've got autumn of time to be playing this right now...",
                      "I hope you're having a gourd time!",
                      "Wait, stay, don't leaf me!",
                      "Just like a vampire, you suck at this...",
                      "You've ghost to be kidding me...",
                      "Is this your idea of skele-fun?",
                      "That was quite spook-tacular",
                      "boo.",
                      "Submit to your Hallow-queen",
                      "I don't mean to scare...",
                      "You in first? Witch-ful thinking...",
                      "You're giving me pumpkin to talk about...",
                      "Howl you doing?",
                      "Bat was something else",
                      "That's a fright for sore eyes",
                      "That really raised my spirits",
                      "Don't mind me, just a spectator... Or maybe a specter",
                      "Take scare of yourself",
                      "Hahaha, you're killing me! Literally...",
                      "Oh jeez, you've got really bat breath...",
                      "That was just brew-tiful",
                      "Keep acting like that and you'll have to stop me from goblin you up!",
                      "zzz, sorry you just remind me of the grim sleeper... zzz",
                      "Fangtastic job",
                      "Whew what a workout, I'm really exorcising over here...",
                      "Un-boo-lievable...",
                      "I don't be-leaf my eyes...",
                      "You can skele-run, but you can't hide...",
                      "That's one for the BOOooks"]
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

        msg_id = await self.executesql('SELECT message_id FROM active_posts WHERE active_id = ?', (activeinfo[0][0],))
        await self.executesql('UPDATE active_posts SET message_id = ? WHERE active_id = ?', (0, activeinfo[0][0]))
        imageinfo = await self.executesql('SELECT r.rarity_name, r.points_first, r.points_second FROM rarities r INNER JOIN images i USING (rarity_id) WHERE i.image_id = ?', (activeinfo[0][2],))
        previouspickup = await self.executesql('SELECT count FROM inventories WHERE (user_id = ? AND server_id = ? AND image_id = ?)', (payload.user_id, payload.guild_id, activeinfo[0][2]))
        if len(previouspickup):
            points = imageinfo[0][2]
        else:
            points = imageinfo[0][1]

        cd = await self.executesql('SELECT last_pickup FROM cooldowns WHERE (active_id = ? AND user_id = ?)', (activeinfo[0][0], payload.user_id))

        if activeinfo[0][1] == 2:
            checkreward = await self.executesql('SELECT reward, start, duration FROM rewards WHERE user_id = ? AND server_id = ?', (payload.user_id, payload.guild_id))
            rewards = self.makerewardslist(checkreward)
            if 4 in rewards:
                points *= 2

        if len(cd):
            cdvalue = 150
            if activeinfo[0][1]:
                if 1 in rewards:
                    cdvalue *= 2
            remaining = cdvalue - (time.time() - cd[0][0])
            if remaining > 0:
                await self.executesql('UPDATE active_posts SET message_id = ? WHERE active_id = ?', (msg_id[0][0], activeinfo[0][0]))
                await (await self.bot.get_guild(payload.guild_id).get_channel(payload.channel_id).fetch_message(payload.message_id)).remove_reaction(payload.emoji, payload.member)
                temp = '{:.0f}'.format(remaining)
                return await self.bot.get_guild(payload.guild_id).get_channel(payload.channel_id).send(f"hold up {payload.member.mention}, you've collected an item too recently, please wait a second to give other users a chance!\nTime remaining: {temp}s")

        pickupstring = 'a'
        if imageinfo[0][0][:1] in ['a', 'e', 'i', 'o', 'u']:
            pickupstring += 'n'

        await self.bot.get_guild(payload.guild_id).get_channel(payload.channel_id).send(f'**{payload.member.mention}, you just picked up {pickupstring} {imageinfo[0][0]} item!**')

        if len(previouspickup) and imageinfo[0][0] != 'common':
            await self.bot.get_guild(payload.guild_id).get_channel(payload.channel_id).send(f'**as you\'ve collected this before, you\'ve earned {imageinfo[0][2]} points!**')
            await Leaderboard.addpoints(self, payload.user_id, payload.guild_id, activeinfo[0][1], points)
        else:
            await self.bot.get_guild(payload.guild_id).get_channel(payload.channel_id).send(f'**you\'ve earned {imageinfo[0][1]} points!**')
            await Leaderboard.addpoints(self, payload.user_id, payload.guild_id, activeinfo[0][1], points)

        if activeinfo[0][1] == 2:
            if 2 in rewards:
                await self.bot.get_guild(payload.guild_id).get_channel(payload.channel_id).send(random.choice(self.SPOOKY_REPLIES))
        await Inventory.additem(self, payload.user_id, payload.guild_id, activeinfo[0][1], activeinfo[0][2], 1)
        await self.executesql('REPLACE INTO cooldowns (active_id, user_id, last_pickup) VALUES (?, ?, ?)', (activeinfo[0][0], payload.user_id, time.time()))
        await Event.eventpost(self, activeinfo[0][0])

    def makerewardslist(self, rewards):
        t = time.time()
        rewardslist = []
        for reward in rewards:
            endtime = reward[1] + reward[2]
            if endtime > t:
                rewardslist.append(reward[0])
        return rewardslist

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
        if len(role):
            role = self.bot.get_guild(payload.guild_id).get_role(role[0][0])
            try:
                if role not in payload.member.roles:
                    await payload.member.add_roles(role)
            except discord.errors.Forbidden:
                await self.bot.get_channel(payload.channel_id).send('I cannot assign you this role as either it is higher than me in the hierarchy or I do not have `manage roles` permissions')

    async def removereactions(self, payload):
        manager = await self.executesql('SELECT manager_id FROM activemanagers WHERE (message_id = ? AND channel_id = ?)', (payload.message_id, payload.channel_id))
        if not len(manager):
            return
        rolelist = await self.executesql('SELECT role_id, emoji FROM roles WHERE manager_id = ?', (manager[0][0],))
        role = [role for role in rolelist if str(role[1]) == str(payload.emoji)]
        member = await self.bot.get_guild(payload.guild_id).fetch_member(payload.user_id)
        if len(role):
            role = self.bot.get_guild(payload.guild_id).get_role(role[0][0])
            if role in member.roles:
                await member.remove_roles(role)
