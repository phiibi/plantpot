#leaderboard.py

import json
import discord
import random

from discord.ext import commands


class Trivia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(help='leaderboard related commands, ".leaderboard help" for more help')
    async def trivia(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('foo bar')
            return


    async def quiz(self, ctx, quizqs, participants):
        questions = Trivia.loadquiz(self, quizqs)
        count = 0

        while (len(questions) > 0):
            count += 1
            q = Trivia.pickquestion(questions)
            questions.remove(q)
            random.shuffle(q['all'])
            colours = []
            embed = discord.Embed()
            embed.title = f'Question {count}'
            qstr = ''
            for i, ans in enumerate(q['all']):
                qstr += f'{ans}\n'
                if ans == q['a']:
                    a = i
            embed.add_field(name=q['q'], value=ans)


    def pickquestion(self, arr):
        return random.choice(arr)

    def loadquiz(self, f):
        with open(f'cogs/quizzes/{f}.json', 'r') as file:
            d = json.loads(file.read())
        return d['questions']