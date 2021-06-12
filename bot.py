#bot.py

import os
import discord
import random

from re import fullmatch, search
from cogs import serversettings, rolemanager

import helpers

from dotenv import load_dotenv
from discord.ext import commands

intents = discord.Intents.all()

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='.', intents=intents)

rolecheck = helpers.ReactionChecker(bot)
eventcheck = helpers.EventChecker(bot)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    print(os.getcwd())
    for guild in bot.guilds:
        print(guild.name)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='photosynthesis'))

@bot.event
async def on_guild_join(guild):
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send('hi there, i\'m plant, a bot made by @Leaf#0077, it\'s nice to meet you!')
        break
    s = serversettings.ServerSetter(guild)
    await s.setupserver()
    print('debug')

@bot.event
async def on_message(message):
    mcl = message.content.lower
    f = open('data/greetings.txt', 'r').readlines()
    greetings = [g.strip() for g in f]

    f = open('data/replies.txt', 'r').readlines()
    replies = [r.strip() for r in f]

    if message.author == bot.user:
        return

    for word in greetings:
        if word + ' plant' in mcl():
            await message.channel.send('{0} {1}'.format(word, message.author.mention))
            break

    if 'plant sus' in mcl():
        await message.channel.send('plant was the imposter... 1 imposter left')

    if 'sorry plant' in mcl():
        replies = ['you better be',
                   'i\'ll forgive you... this time',
                   'you\'ll be hearing from my lawyer',
                   'i forgive you!',
                   'no worries',
                   'no problem',
                   'it\'s ok',
                   'i won\'t forget about this...']
        await message.channel.send(random.choice(replies))

    if 'milf' in mcl():
        r = random.random();
        if r > 0.9:
            await message.channel.send('i want big mummy milkers')

    if 'how are you plant' in mcl():
        await message.channel.send(random.choice(replies))

    if 'gang gang' in mcl():
        await message.channel.send('gang shit')

    if 'how many greetings do you have' in mcl():
        await message.channel.send(f'i can greet you in {len(greetings)} different ways, can you find them all?')

    if fullmatch('.*(((love you|ily)\s+(plant))|((plant)\s+(love you|ily))).*', mcl()):
        await message.channel.send(f'i love you too {message.author.mention}')

    if 'bugged' in mcl():
        await message.channel.send('it\'s not a bug, it\'s a feature')

    if 'plant bias' in mcl():
        replies = ['i\'m not bias, you\'re just bad',
                   'it\'s not bias if it\'s true',
                   'i don\'t get paid enough for this...']
        await message.channel.send(random.choice(replies))

    if 'pog' in mcl():
        if 'aggressive' in mcl():
            await message.channel.send('**pog**')
        elif 'poggers' in mcl():
            await message.channel.send('poggers')
        elif search('\s*(pog)(ging|[^\w]|$)', mcl()):
            await message.channel.send('pog')

    if mcl() == 'good bot':
        await message.channel.send('good user')

    if fullmatch('(thank you|ty)\s(plant)', mcl()):
        await message.channel.send('you\'re welcome ' + message.author.mention)

    if mcl() == 'and i oop':
        await message.channel.send('sksksk')

    if mcl() == 'f':
        await message.channel.send('f')

    if mcl() == 'ue':
        await message.channel.send('ue')

    if mcl() == 'owa owa' or search('(can i get an owa owa)', mcl()):
        await message.channel.send('owa owa')

    await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.member == bot.user:
        return
    await rolecheck.addreactions(payload)
    await eventcheck.eventcollect(payload)

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.member == bot.user:
        return
    await rolecheck.removereactions(payload)

bot.load_extension('cogs.interactive')
bot.load_extension('cogs.event')
bot.load_extension('cogs.crafting')
bot.load_extension('cogs.imageposting')
bot.load_extension('cogs.leaderboard')
bot.load_extension('cogs.inventory')
bot.load_extension('cogs.profile')
bot.load_extension('cogs.serversettings')
bot.load_extension('cogs.admin')
bot.load_extension('cogs.anime')
bot.load_extension('cogs.badges')
bot.load_extension('cogs.flowers')
bot.load_extension('cogs.quiz')
bot.load_extension('cogs.premium')
bot.load_extension('cogs.misc')
bot.load_extension('cogs.reminder')
bot.load_extension('cogs.rolemanager')
bot.run(TOKEN)
