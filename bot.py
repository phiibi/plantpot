#bot.py

import os
import discord
import random
from re import fullmatch, search
from cogs import interactive, imageposting, leaderboard, inventory, profile, serversettings, admin

from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!!')



@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    print(os.getcwd())
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='photosynthesis'))

@bot.event
async def on_guild_join(guild):
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send('hi there, i\'m plant, a bot made by @Leaf#0077, it\'s nice to meet you!')
        break
    await serversettings.ServerSettings.setupserver()

@bot.event
async def on_message(message):
    mcl = message.content.lower
    replies = ['hello', 'hey', 'heyy', 'hi', 'wagwan', 'what\'s poppin', 'what\'s poppin\'', 'hola', 'buenos dias', 'konnichiwa', 'ohayo',
               'bonjour', 'salut', 'buongiorno', 'buon giorno', 'good morning', 'gm', 'good night', 'goodnight', 'ohayo gozaimasu',
               'gn','guten tag', 'guten morgen', 'privet', 'zdravstvuyte', 'ciao', 'ni hao', 'annyeong', 'anyeong haseyo', 'hallo',
               'shalom', 'hej', 'sup', 'wassup', 'namaste', 'czesc', 'ayo', 'yo', 'g\'day', 'good day', 'aloha', 'y\'alright', 'what ho',
               'god dag',  'howdy', 'what\'s up', 'hai', 'gday', 'yassou', 'o/', 'salutations', 'greetings', 'whats gwaning', 'howzit',
               'what\'s gwaning', 'wazzup', 'wazup', 'whats up', 'henlo', 'heyo', 'salam', 'salaam', 'hey~', 'namaskaram', 'how\'s it hanging', 'how\'s it hangin',
               'hoi', 'oi', 'hei', 'dap me up', 'ola', 'whats good', 'what\'s good', 'good evening', 'good afternoon', 'god morgen',
               'what it be', 'good morrow', 'what\'s crackalackin', 'morning', 'afternoon', 'evening', 'night', 'coucou', 'hewwo', 'how\'s it going']
    plantreplies = ['it\'s one of rose days...', 'i\'m well, you asking me has made my daisy', 'sorting out my weed issue once and floral'
                    'i\'m feeling clover the moon!', 'i\'m well, how\'s it growing?', 'i was hoping some-bud-y would ask me that',
                    'lilac that you asked me that', 'i\'m doing bouquet', 'i\'m feeling dandy, i\'m not lion!', 'feeling a lily better now that you\'ve asked me',
                    'a pot better now you\'re here!', 'i really seed a break...', 'feeling a sense of impending bloom...',
                    'i\'m gladiola you asked', 'i\'m well, thistle be a great day', 'aloe, i\'m doing great', 'i be-leaf this\'ll be a great day!',
                    'iris-ed you']

    if message.author == bot.user:
        return

    for word in replies:
        if word + ' plant' in mcl():
            await message.channel.send('{0} {1}'.format(word, message.author.mention))
            break

    if 'plant sus' in mcl():
        await message.channel.send('plant was the imposter... 1 imposter left')

    if 'milf' in mcl():
        r = random.random();
        if r > 0.9:
            await message.channel.send('i want big mummy milkers')

    if 'how are you plant' in mcl():
        await message.channel.send(random.choice(plantreplies))

    if 'gang gang' in mcl():
        await message.channel.send('gang shit')

    if 'how many greetings do you have' in mcl():
        await message.channel.send(f'i can greet you in {len(replies)} different ways, can you find them all?')

    if fullmatch('.*(love you|ily|plant)\s+(love you|ily|plant).*', mcl()):
        await message.channel.send(f'i love you too {message.author.mention}')

    if 'bugged' in mcl():
        await message.channel.send('it\'s not a bug, it\'s a feature')

    if 'plant bias' in mcl():
        replies = ['i\'m not bias, you\'re just bad',
                   'it\'s not bias if it\'s true,'
                   'i don\'t get paid enough for this...']
        await message.channel.send(random.choice(replies))

    if 'pog' in mcl():
        if 'aggressive' in mcl():
            await message.channel.send('**pog**')
        elif 'poggers' in mcl():
            await message.channel.send('poggers')
        elif search('\s*(pog)(\s+|$)', mcl()):
            await message.channel.send('pog')

    if mcl == 'good bot':
        await message.channel.send('good user')

    if mcl() == 'thank you plant':
        await message.channel.send('you\'re welcome ' + message.author.mention)

    if mcl() == 'and i oop':
        await message.channel.send('sksksk')

    await bot.process_commands(message)


bot.load_extension('cogs.interactive')
bot.load_extension('cogs.imageposting')
bot.load_extension('cogs.leaderboard')
bot.load_extension('cogs.inventory')
bot.load_extension('cogs.profile')
bot.load_extension('cogs.serversettings')
bot.load_extension('cogs.admin')
bot.load_extension('cogs.anime')
bot.load_extension('cogs.badges')
bot.load_extension('cogs.flowers')
bot.run(TOKEN)
