# -----  Matthew Hammond, 2021  -----
# ----  Plant Bot Quiz Commands  ----
# -------------  v1.0  --------------


import discord
from discord.ext import commands
import asyncio

from sqlite3 import connect
from datetime import datetime
from random import shuffle

class Quiz(commands.Cog):

    conn = connect("database.db")
    cursor = conn.cursor()

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
    DEFAULT_ANSWER_EMOJIS = ["🇦", "🇧", "🇨", "🇩"]
    
    def __init__(self, bot):
        
        self.bot = bot

        self.executeSQL("PRAGMA foreign_keys = ON")
        # Allows foreign keys.

        self.executeSQL("""
            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY,
                server INTEGER NOT NULL,
                name TEXT NOT NULL
            )
        """)
        self.executeSQL("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY,
                quiz INTEGER NOT NULL,
                text TEXT NOT NULL,
                CONSTRAINT fk_quiz FOREIGN KEY (quiz) REFERENCES quizzes(id) ON DELETE CASCADE
            )
        """)
        self.executeSQL("""
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY,
                question INTEGER NOT NULL,
                text TEXT NOT NULL,
                emoji TEXT NOT NULL,
                correct INTEGER NOT NULL,
              CONSTRAINT fk_question FOREIGN KEY (question) REFERENCES questions(id) ON DELETE CASCADE
            )
        """)

    def executeSQL(self, statement, data = ()):

        self.cursor.execute(statement, data)
        self.conn.commit()
        return self.cursor.fetchall()

    async def quizWizardCheck(ctx):
        return ctx.author.permissions_in(ctx.channel).manage_guild or 825241813505802270 in [role.id for role in ctx.author.roles]
        # Must have the Plant Team role to use the quiz wizard.

    async def quizcheck(ctx):
        return ctx.guild.id == 813532137050341407

    @commands.command(
        name = "quizwizard",
        aliases = ["quizwiz", "qw"],

        brief = "Create and edit quizzes.",
        description = "Create and edit quizzes, questions, and answers for this server.\nRequires the user to have the Manage Server permission.",
        help = "Premium is required for custom emojis, more quizzes, and more questions per quiz.",
        
        usage = "quizwizard",
    )
    @commands.check(quizWizardCheck)
    async def quizWizard(self, ctx):

        embed = discord.Embed(
            title = "Quiz Wizard",
            description = "Loading...",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        msg = await ctx.send(embed = embed)

        for emoji in self.EMOJIS.values():
            await msg.add_reaction(emoji)

        await self.mainMenu(ctx, msg)

        embed = discord.Embed(
            title = "Quiz Wizard",
            description = "Finished.",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        await msg.edit(embed = embed)

    async def mainMenu(self, ctx, msg):

        def check(reaction, user):
            return ctx.author.id == user.id and msg.id == reaction.message.id

        availableQuizzes = self.executeSQL("""
            SELECT id, name FROM quizzes
            WHERE server = ?
        """, (ctx.guild.id,))
        page = 0

        while True:

            embed = discord.Embed(
                title = "Quiz Wizard - Select a quiz.",
                description = "React with a number to select a quiz.\nReact with :arrow_left: to go back a page.\nReact with :arrow_right: to go forward a page.\nReact with :new: to create a new quiz.\nReact with :eject: to quit.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            if (len(availableQuizzes)):
                embed.add_field(
                    name = "Available Quizzes (" + str(page * 10 + 1) + "-" + str(min(page * 10 + 10, len(availableQuizzes))) + "/" + str(len(availableQuizzes)) + ")",
                    value = "\n".join(self.EMOJIS[str(i)] + " " + availableQuizzes[page*10 + i][1] for i in range(0, len(availableQuizzes[page*10:page*10+10])))
                )
            else:
                embed.add_field(
                    name = "Available Quizzes (0-0/0)",
                    value = "None",
                )
            await msg.edit(embed = embed)

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = check)
            except asyncio.TimeoutError:
                return
            await msg.remove_reaction(reaction, user)

            if (reaction.emoji == self.EMOJIS["left_arrow"]):
                page -= 1
                page %= (len(availableQuizzes) // 10 + 1)

            elif (reaction.emoji == self.EMOJIS["right_arrow"]):
                page += 1
                page %= (len(availableQuizzes) // 10 + 1)

            elif (reaction.emoji == self.EMOJIS["new"]):
                await self.newQuiz(ctx, msg)
                availableQuizzes = self.executeSQL("""
                    SELECT id, name FROM quizzes
                    WHERE server = ?
                """, (ctx.guild.id,))
                page = 0

            elif (reaction.emoji == self.EMOJIS["eject"]):
                return

            elif (reaction.emoji in self.EMOJIS.values()):
                if (page*10 + int(reaction.emoji[0]) < len(availableQuizzes)):
                    await self.quizMenu(ctx, msg, availableQuizzes[page*10 + int(reaction.emoji[0])][0])
                    availableQuizzes = self.executeSQL("""
                        SELECT id, name FROM quizzes
                        WHERE server = ?
                    """, (ctx.guild.id,))
                    page = 0

    async def newQuiz(self, ctx, msg):

        def text_check(msg):
            return ctx.author.id == msg.author.id

        def reaction_check(reaction, user):
            return reaction.emoji == self.EMOJIS["eject"] and ctx.author.id == user.id

        if (len(self.executeSQL("""
            SELECT id FROM premiumServers
            WHERE id = ?
        """, (ctx.guild.id,))) or
            not len(self.executeSQL("""
                SELECT id FROM quizzes
                WHERE server = ?
            """, (ctx.guild.id,)))):

            embed = discord.Embed(
                title = "Quiz Wizard - Create a quiz.",
                description = "Reply with the name of the quiz.\nWait 60s to cancel.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(), 
            )
            await msg.edit(embed = embed)

            try:
                quizName = await self.bot.wait_for("message", timeout = 60, check = text_check)
            except asyncio.TimeoutError:
                return
            await quizName.delete()
            quizName = quizName.content

            usedQuizNames = [quiz[0] for quiz in self.executeSQL("""
                SELECT name FROM quizzes
                WHERE server = ?
            """, (ctx.guild.id,))]

            if (quizName in usedQuizNames):
                embed = discord.Embed(
                    title = "Quiz Wizard - Create a quiz.",
                    description = "\"{}\" is already being used in this server.\nReact with :eject: or wait 60s to go back.".format(quizName),
                    colour = ctx.guild.get_member(self.bot.user.id).colour,
                    timestamp = datetime.now(),
                )
                await msg.edit(embed = embed)

                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = reaction_check)
                except asyncio.TimeoutError:
                    return
                await msg.remove_reaction(reaction, user)
                return

            else:
                self.executeSQL("""
                    INSERT INTO quizzes (server, name)
                    VALUES (?, ?)
                """, (ctx.guild.id, quizName))

                quizId = self.executeSQL("""
                    SELECT id FROM quizzes
                    WHERE (server = ? AND name = ?)
                """, (ctx.guild.id, quizName))[0][0]

                await self.quizMenu(ctx, msg, quizId)

        else:
            embed = discord.Embed(
                title = "Quiz Wizard - Create a quiz.",
                description = "You need to purchase premium to have more than 1 quiz per server.\nReact with :eject: or wait 60s to go back.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            await msg.edit(embed = embed)

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = reaction_check)
            except asyncio.TimeoutError:
                return
            await msg.remove_reaction(reaction, user)
            return

    async def quizMenu(self, ctx, msg, quizId):

        def check(reaction, user):
            return ctx.author.id == user.id and msg.id == reaction.message.id

        availableQuestions = self.executeSQL("""
            SELECT id, text FROM questions
            WHERE quiz = ?
        """, (quizId,))
        page = 0

        while True:

            embed = discord.Embed(
                title = "Quiz Wizard - Select a question.",
                description = "React with a number to select a question.\nReact with :arrow_left: to go back a page.\nReact with :arrow_right: to go forward a page.\nReact with :new: to create a new question.\nReact with :record_button: to change the quiz name.\nReact with :asterisk: to delete the quiz.\nReact with :eject: to go back.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            if (len(availableQuestions)):
                embed.add_field(
                    name = "Available Questions (" + str(page * 10 + 1) + "-" + str(min(page * 10 + 10, len(availableQuestions))) + "/" + str(len(availableQuestions)) + ")",
                    value = "\n".join(self.EMOJIS[str(i)] + " " + availableQuestions[page*10 + i][1] for i in range(0, len(availableQuestions[page*10:page*10+10])))
                )
            else:
                embed.add_field(
                    name = "Available Questions (0-0/0)",
                    value = "None",
                )
            await msg.edit(embed = embed)

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = check)
            except asyncio.TimeoutError:
                return
            await msg.remove_reaction(reaction, user)

            if (reaction.emoji == self.EMOJIS["left_arrow"]):
                page -= 1
                page %= (len(availableQuestions) // 10 + 1)

            elif (reaction.emoji == self.EMOJIS["right_arrow"]):
                page += 1
                page %= (len(availableQuestions) // 10 + 1)

            elif (reaction.emoji == self.EMOJIS["new"]):
                await self.newQuestion(ctx, msg, quizId)
                availableQuestions = self.executeSQL("""
                    SELECT id, text FROM questions
                    WHERE quiz = ?
                """, (quizId,))
                page = 0

            elif (reaction.emoji == self.EMOJIS["record_button"]):
                await self.changeQuizName(ctx, msg, quizId)

            elif (reaction.emoji == self.EMOJIS["asterisk"]):
                if (await self.deleteQuiz(ctx, msg, quizId)):
                    return

            elif (reaction.emoji == self.EMOJIS["eject"]):
                return

            elif (reaction.emoji in self.EMOJIS.values()):
                if (page*10 + int(reaction.emoji[0]) < len(availableQuestions)):
                    await self.questionMenu(ctx, msg, availableQuestions[page*10 + int(reaction.emoji[0])][0])
                    availableQuestions = self.executeSQL("""
                        SELECT id, text FROM questions
                        WHERE quiz = ?
                    """, (quizId,))
                    page = 0

    async def changeQuizName(self, ctx, msg, quizId):

        def check(msg):
            return ctx.author.id == msg.author.id

        data = self.executeSQL("""
            SELECT name FROM quizzes
            WHERE id = ?
        """, (quizId,))[0][0]

        embed = discord.Embed(
            title = "Quiz Wizard - Edit a quiz.",
            description = "Reply with the quiz name.\nWait 60s to cancel.",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        embed.add_field(name = "Old Value", value = data)
        await msg.edit(embed = embed)

        try:
            quizName = await self.bot.wait_for("message", timeout = 60, check = check)
        except asyncio.TimeoutError:
            return
        await quizName.delete()
        quizName = quizName.content

        self.executeSQL("""
            UPDATE questions
            SET text = ?
            WHERE id = ?
        """, (quizName, quizId))

    async def deleteQuiz(self, ctx, msg, quizId):

        def check(msg):
            return ctx.author.id == msg.author.id
        
        embed = discord.Embed(
            title = "Quiz Wizard - Deleting a quiz.",
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
            DELETE FROM quizzes
            WHERE id = ?
        """, (quizId,))

        return True

    async def newQuestion(self, ctx, msg, quizId):

        def check(msg):
            return ctx.author.id == msg.author.id

        if (len(self.executeSQL("""
            SELECT id FROM premiumServers
            WHERE id = ?
        """, (ctx.guild.id,))) or
            len(self.executeSQL("""
                SELECT id FROM questions
                WHERE quiz = ?
            """, (quizId,))) < 10):

            embed = discord.Embed(
                title = "Quiz Wizard - Create a question.",
                description = "Reply with the question.\nWait 60s to cancel.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            await msg.edit(embed = embed)

            try:
                questionText = await self.bot.wait_for("message", timeout = 60, check = check)
            except asyncio.TimeoutError:
                return
            await questionText.delete()
            questionText = questionText.content

            self.executeSQL("""
                INSERT INTO questions (quiz, text)
                VALUES (?, ?)
            """, (quizId, questionText))

            questionId = self.executeSQL("""
                SELECT id FROM questions
                WHERE (quiz = ? AND text = ?)
            """, (quizId, questionText))[0][0]

            await self.questionMenu(ctx, msg, questionId)

        else:
            embed = discord.Embed(
                title = "Quiz Wizard - Create a question.",
                description = "You need to purchase premium to have more than 10 questions per quiz.\nReact with :eject: or wait 60s to go back.",
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

    async def questionMenu(self, ctx, msg, questionId):
        
        def check(reaction, user):
            return user.id == ctx.author.id and msg.id == reaction.message.id

        availableAnswers = self.executeSQL("""
            SELECT id, text, emoji, correct FROM answers
            WHERE question = ?
        """, (questionId,))
        page = 0

        while True:

            embed = discord.Embed(
                title = "Quiz Wizard - Select an answer.",
                description = "React with a number to select an answer.\nReact with :arrow_left: to go back a page.\nReact with :arrow_right: to go forward a page.\nReact with :new: to create a new answer.\nReact with :record_button: to change the question text.\nReact with :asterisk: to delete the question.\nReact with :eject: to go back.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            if (len(availableAnswers)):
                embed.add_field(
                    name = "Available Answers (" + str(page * 10 + 1) + "-" + str(min(page * 10 + 10, len(availableAnswers))) + "/" + str(len(availableAnswers)) + ")",
                    value = "\n".join("{} {} ({}, {})".format(self.EMOJIS[str(i)], availableAnswers[page*10 + i][1], availableAnswers[page*10 + i][2], bool(availableAnswers[page*10 + i][3])) for i in range(0, len(availableAnswers[page*10:page*10+10])))
                )
            else:
                embed.add_field(
                    name = "Available Answers (0-0/0)",
                    value = "None",
                )
            await msg.edit(embed = embed)

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = check)
            except asyncio.TimeoutError:
                return
            await msg.remove_reaction(reaction, user)

            if (reaction.emoji == self.EMOJIS["left_arrow"]):
                page -= 1
                page %= (len(availableQuizzes) // 10 + 1)

            elif (reaction.emoji == self.EMOJIS["right_arrow"]):
                page += 1
                page %= (len(availableQuizzes) // 10 + 1)

            elif (reaction.emoji == self.EMOJIS["new"]):
                await self.newAnswer(ctx, msg, questionId)
                availableAnswers = self.executeSQL("""
                    SELECT id, text, emoji, correct FROM answers
                    WHERE question = ?
                """, (questionId,))
                page = 0

            elif (reaction.emoji == self.EMOJIS["record_button"]):
                await self.changeQuestionText(ctx, msg, questionId)

            elif (reaction.emoji == self.EMOJIS["asterisk"]):
                if (await self.deleteQuestion(ctx, msg, questionId)):
                    return

            elif (reaction.emoji == self.EMOJIS["eject"]):
                return

            elif (reaction.emoji in self.EMOJIS.values()):
                if (page*10 + int(reaction.emoji[0]) < len(availableAnswers)):
                    await self.answerMenu(ctx, msg, availableAnswers[page*10 + int(reaction.emoji[0])][0])
                    availableAnswers = self.executeSQL("""
                        SELECT id, text, emoji, correct FROM answers
                        WHERE question = ?
                    """, (questionId,))
                    page = 0

    async def changeQuestionName(self, ctx, msg, questionId):

        def check(msg):
            return ctx.author.id == msg.author.id

        data = self.executeSQL("""
            SELECT quiz.name, questions.text FROM questions
            INNER JOIN quiz ON quiz.id = questions.quiz 
            WHERE questions.id = ?
        """, (questionId,))[0]

        embed = discord.Embed(
            title = "Quiz Wizard - Edit a question.",
            description = "Reply with the question.\nWait 60s to cancel.",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        embed.add_field(name = "Quiz", value = data[0])
        embed.add_field(name = "Old Value", value = data[1])
        await msg.edit(embed = embed)

        try:
            questionText = await self.bot.wait_for("message", timeout = 60, check = check)
        except asyncio.TimeoutError:
            return
        await questionText.delete()
        questionText = questionText.content

        self.executeSQL("""
            UPDATE questions
            SET text = ?
            WHERE id = ?
        """, (questionText, questionId))

    async def deleteQuestion(self, ctx, msg, questionId):

        def check(msg):
            return ctx.author.id == msg.author.id
        
        embed = discord.Embed(
            title = "Quiz Wizard - Deleting a question.",
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
            DELETE FROM questions
            WHERE id = ?
        """, (questionId,))

        return True

    async def newAnswer(self, ctx, msg, questionId):

        def text_check(msg):
            return ctx.author.id == msg.author.id

        def emoji_check(reaction, user):
            return ctx.author.id == user.id and msg.id == reaction.message.id

        def correct_check(msg):
            return ctx.author.id == msg.author.id
            
        if (len(self.executeSQL("""
            SELECT id FROM premiumServers
            WHERE id = ?
        """, (ctx.guild.id,))) or
            len(self.executeSQL("""
                SELECT id FROM answers
                WHERE question = ?
            """, (questionId,))) < 4):

            embed = discord.Embed(
                title = "Quiz Wizard - Create an answer.",
                description = "Reply with the answer.\nWait 60s to cancel.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            await msg.edit(embed = embed)

            try:
                answerText = await self.bot.wait_for("message", timeout = 60, check = text_check)
            except asyncio.TimeoutError:
                return
            await answerText.delete()
            answerText = answerText.content

            if (len(self.executeSQL("""
                SELECT id FROM premiumServers
                WHERE id = ?
            """, (ctx.guild.id,)))):

                embed = discord.Embed(
                    title = "Quiz Wizard - Create an answer.",
                    description = "React with the answers's emoji.\nWait 60s to cancel.",
                    colour = ctx.guild.get_member(self.bot.user.id).colour,
                    timestamp = datetime.now(),
                )
                await msg.edit(embed = embed)

                try:
                    answerEmoji, user = await self.bot.wait_for("reaction_add", timeout = 60, check = emoji_check)
                except asyncio.TimeoutError:
                    return
                await msg.remove_reaction(answerEmoji, user)
                answerEmoji = answerEmoji.emoji

            else:
                answerEmoji = self.DEFAULT_ANSWER_EMOJIS[len(self.executeSQL("""
                    SELECT * FROM answers
                    WHERE question = ?
                """, (questionId,)))]

            embed = discord.Embed(
                title = "Quiz Wizard - Create an answer.",
                description = "Is the answer correct? (Y/N)\nWait 60s to cancel.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            await msg.edit(embed = embed)

            try:
                answerCorrect = await self.bot.wait_for("message", timeout = 60, check = correct_check)
            except asyncio.TimeoutError:
                return
            await answerCorrect.delete()
            answerCorrect = int(answerCorrect.content.lower()[0] == "y")

            self.executeSQL("""
                INSERT INTO answers (question, text, emoji, correct)
                VALUES (?, ?, ?, ?)
            """, (questionId, answerText, answerEmoji, answerCorrect))

        else:
            embed = discord.Embed(
                title = "Quiz Wizard - Create an answer.",
                description = "You need to purchase premium to have more than 4 answers per question.\nReact with :eject: or wait 60s to go back.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            await msg.edit(embed = embed)

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = emoji_check)
            except asyncio.TimeoutError:
                return
            await msg.remove_reaction(reaction, user)
            return

    async def answerMenu(self, ctx, msg, answerId):
        
        def check(reaction, user):
            return user.id == ctx.author.id and reaction.emoji in self.EMOJIS.values()
        
        answer = self.executeSQL("""
            SELECT text, emoji, correct FROM answers
            WHERE id = ?
        """, (answerId,))[0]

        while True:

            embed = discord.Embed(
                title = "Quiz Wizard - Select an answer.",
                description = "React with :zero: to change the text.\nReact with :one: to change the emoji.\nReact with :two: to change if it is correct.\nReact with :asterisk: to delete the answer.\nReact with :eject: to go back.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            embed.add_field(name = "Text", value = answer[0])
            embed.add_field(name = "Emoji", value = answer[1])
            embed.add_field(name = "Correct?", value = bool(answer[2]))
            await msg.edit(embed = embed)

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout = 60, check = check)
            except asyncio.TimeoutError:
                return
            await msg.remove_reaction(reaction, user)

            if (reaction.emoji == self.EMOJIS["asterisk"]):
                if (await self.deleteAnswer(ctx, msg, answerId)):
                    return

            elif (reaction.emoji == self.EMOJIS["eject"]):
                return

            elif (reaction.emoji == self.EMOJIS["0"]):
                await self.changeAnswerText(ctx, msg, answerId)
                answer = self.executeSQL("""
                    SELECT text, emoji, correct FROM answers
                    WHERE id = ?
                """, (answerId,))[0]

            elif (reaction.emoji == self.EMOJIS["1"]):
                await self.changeAnswerEmoji(ctx, msg, answerId)
                answer = self.executeSQL("""
                    SELECT text, emoji, correct FROM answers
                    WHERE id = ?
                """, (answerId,))[0]

            elif (reaction.emoji == self.EMOJIS["2"]):
                await self.changeAnswerCorrect(ctx, msg, answerId)
                answer = self.executeSQL("""
                    SELECT text, emoji, correct FROM answers
                    WHERE id = ?
                """, (answerId,))[0]

    async def deleteAnswer(self, ctx, msg, answerId):

        def check(msg):
            return ctx.author.id == msg.author.id
        
        embed = discord.Embed(
            title = "Quiz Wizard - Deleting an answer.",
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
            DELETE FROM answers
            WHERE id = ?
        """, (answerId,))

        return True

    async def changeAnswerText(self, ctx, msg, answerId):

        def check(msg):
            return ctx.author.id == msg.author.id

        data = self.executeSQL("""
            SELECT questions.text, answers.text FROM answers
            INNER JOIN questions ON questions.id = answers.question
            WHERE answers.id = ?
        """, (answerId,))[0]

        embed = discord.Embed(
            title = "Quiz Wizard - Edit an answer.",
            description = "Reply with the answer.\nWait 60s to cancel.",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        embed.add_field(name = "Question", value = data[0])
        embed.add_field(name = "Old Value", value = data[1])
        await msg.edit(embed = embed)

        try:
            answerText = await self.bot.wait_for("message", timeout = 60, check = check)
        except asyncio.TimeoutError:
            return
        await answerText.delete()
        answerText = answerText.content

        self.executeSQL("""
            UPDATE answers
            SET text = ?
            WHERE id = ?
        """, (answerText, answerId))

    async def changeAnswerEmoji(self, ctx, msg, answerId):

        def check(reaction, user):
            return ctx.author.id == user.id and msg.id == reaction.message.id
            
        if (len(self.executeSQL("""
            SELECT id FROM premiumServers
            WHERE id = ?
        """, (ctx.guild.id,)))):

            data = self.executeSQL("""
                SELECT questions.text, answers.emoji FROM answers
                INNER JOIN questions ON questions.id = answers.question
                WHERE answers.id = ?
            """, (answerId,))[0]

            embed = discord.Embed(
                title = "Quiz Wizard - Edit an answer.",
                description = "React with the answer's emoji.\nWait 60s to cancel.",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            embed.add_field(name = "Question", value = data[0])
            embed.add_field(name = "Old Value", value = data[1])
            await msg.edit(embed = embed)

            try:
                answerEmoji, user = await self.bot.wait_for("reaction_add", timeout = 60, check = check)
            except asyncio.TimeoutError:
                return
            await msg.remove_reaction(answerEmoji, user)
            answerEmoji = answerEmoji.emoji

            self.executeSQL("""
                UPDATE answers
                SET emoji = ?
                WHERE id = ?
            """, (answerEmoji, answerId))

        else:
            embed = discord.Embed(
                title = "Quiz Wizard - Edit an answer.",
                description = "You need to purchase premium to customise answer emojis.\nReact with :eject: or wait 60s to go back.",
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

    async def changeAnswerCorrect(self, ctx, msg, answerId):

        def check(msg):
            return ctx.author.id == msg.author.id

        data = self.executeSQL("""
            SELECT questions.text, answers.correct FROM answers
            INNER JOIN questions ON questions.id = answers.question
            WHERE answers.id = ?
        """, (answerId,))[0]

        embed = discord.Embed(
            title = "Quiz Wizard - Edit an answer.",
            description = "Is the answer correct? (Y/N)\nWait 60s to cancel.",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        embed.add_field(name = "Question", value = data[0])
        embed.add_field(name = "Old Value", value = data[1])
        await msg.edit(embed = embed)

        try:
            answerCorrect = await self.bot.wait_for("message", timeout = 60, check = check)
        except asyncio.TimeoutError:
            return
        await answerCorrect.delete()
        answerCorrect = int(answerCorrect.content.lower()[0] == "y")

        self.executeSQL("""
            UPDATE answers
            SET correct = ?
            WHERE id = ?
        """, (answerText, answerId))

    @commands.command(
        name = "quiz",
        aliases = ["q"],

        brief = "Take a quiz!",
        description = "Take a quiz!",
        help = "\"quiz help\" for a list of parameters.\n\"quiz list\" for a list of available quizzes.",
        
        usage = "quiz [help|list|<name>] {parameters}",
    )
    @commands.check(quizcheck)
    async def quiz(self, ctx, *args):

        def check(msg):
            return ctx.author.id == msg.author.id

        if (len(args) == 0 or args[0] in ["h", "help"]):
            await self.quizHelp(ctx)

        elif (args[0] in ["l", "list"]):
            await self.quizList(ctx)
            
        elif (args[0] in ["w", "wizard"]):
            await self.quizWizard(ctx)

        else:
            embed = discord.Embed(
                title = "Quiz",
                description = "Loading...",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            msg = await ctx.send(embed = embed)

            args = " ".join(args).split(" -")

            quizId = self.executeSQL("""
                SELECT id FROM quizzes
                WHERE server = ? AND name = ?
            """, (ctx.guild.id, args[0]))

            if (not len(quizId) or
                not len(self.executeSQL("""
                    SELECT DISTINCT quizzes.id FROM quizzes
                    INNER JOIN questions ON quizzes.id = questions.quiz
                    INNER JOIN answers ON questions.id = answers.question
                    WHERE quizzes.id = ? AND answers.correct = 1
                """, (quizId[0][0],)))):
                embed = discord.Embed(
                    title = "Quiz Error",
                    description = "Invalid Quiz Name: \"{}\"\nUse \"quiz list\" to see a list of available quizzes in this server.".format(args[0]),
                    colour = ctx.guild.get_member(self.bot.user.id).colour,
                    timestamp = datetime.now(),
                )
                await msg.edit(embed = embed)
                return
            
            quizId = quizId[0][0]

            mode = "s"
            random = False
            time = 60
            gap = 10

            for arg in args[1:]:
                arg = arg.split(" ")
                cmd = arg[0]
                arg = arg[1:]

                if (cmd in ["s", "speed", "a", "accuracy"]):
                    mode = cmd[0]

                elif (cmd in ["t", "time"]):
                    try:
                        if (arg[0][-1] == "s"):
                            arg[0] = arg[0][:-1]
                        time = int(arg[0])

                    except ValueError:
                        embed = discord.Embed(
                            title = "Quiz Error",
                            description = "Invalid Time Value: \"{}\"\nContinue Anyway? (Y/N)".format(arg[0]),
                            colour = ctx.guild.get_member(self.bot.user.id).colour,
                            timestamp = datetime.now(),
                        )
                        await msg.edit(embed = embed)

                        try:
                            cont = await self.bot.wait_for("message", timeout = 60, check = check)
                        except asyncio.TimeoutError:
                            return
                        await cont.delete()

                        if (cont.content.lower()[0] != "y"):
                            return

                        embed = discord.Embed(
                            title = "Quiz",
                            description = "Loading...",
                            colour = ctx.guild.get_member(self.bot.user.id).colour,
                            timestamp = datetime.now(),
                        )
                        await msg.edit(embed = embed)

                elif (cmd in ["g", "gap"]):
                    try:
                        if (arg[0][-1] == "s"):
                            arg[0] = arg[0][:-1]
                        gap = int(arg[0])

                    except ValueError:
                        embed = discord.Embed(
                            title = "Quiz Error",
                            description = "Invalid Gap Value: \"{}\"\nContinue Anyway? (Y/N)".format(arg[0]),
                            colour = ctx.guild.get_member(self.bot.user.id).colour,
                            timestamp = datetime.now(),
                        )
                        await msg.edit(embed = embed)

                        try:
                            cont = await self.bot.wait_for("message", timeout = 60, check = check)
                        except asyncio.TimeoutError:
                            return
                        await cont.delete()

                        if (cont.content.lower()[0] != "y"):
                            return

                        embed = discord.Embed(
                            title = "Quiz",
                            description = "Loading...",
                            colour = ctx.guild.get_member(self.bot.user.id).colour,
                            timestamp = datetime.now(),
                        )
                        await msg.edit(embed = embed)

                elif (cmd in ["r", "random"]):
                    random = True

            scores, maxPossibleScore = await self.quizLoop(ctx, msg, quizId, mode, random, time, gap)
            highScore = 1
            winnerMentions = []
            for userMention, score in scores.items():
                if (score > highScore):
                    highScore = score
                    winnerMentions = []
                if (score == highScore):
                    winnerMentions.append(userMention)

            embed = discord.Embed(
                title = "Quiz Results",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            if (len(winnerMentions)):
                embed.add_field(name = "{} Winner{}! (Score of {}/{})".format(len(winnerMentions), "" if len(winnerMentions) == 1 else "s", highScore, maxPossibleScore), value = "\n".join([self.bot.get_user(userMention).mention if (self.bot.get_user(userMention)) else str(userMention) for userMention in winnerMentions]))
            else:
                embed.add_field(name = "No Winners!", value = "No one scored any points!")
            await msg.edit(embed = embed)

    async def quizLoop(self, ctx, msg, quizId, mode, random, time, gap):

        questionData = self.executeSQL("""
            SELECT id, text FROM questions
            WHERE quiz = ?
        """, (quizId,))

        if (random):
            shuffle(questionData)

        scores = {}

        for question in questionData:

            embed = discord.Embed(
                title = question[1],
                description = "Loading...",
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            await msg.edit(embed = embed)

            answerData = self.executeSQL("""
                SELECT text, emoji, correct FROM answers
                WHERE question = ?
            """, (question[0],))

            if (random):
                shuffle(answerData)

            correctEmojis = []
            await msg.clear_reactions()
            for answer in answerData:
                if (answer[2]):
                    correctEmojis.append(answer[1])
                await msg.add_reaction(answer[1])

            embed = discord.Embed(
                title = question[1],
                description = "\n".join(["{} {}".format(answer[1], answer[0]) for answer in answerData]),
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )
            await msg.edit(embed = embed)
                
            embed = discord.Embed(
                title = question[1],
                colour = ctx.guild.get_member(self.bot.user.id).colour,
                timestamp = datetime.now(),
            )

            if (mode == "s"):
                def check(reaction, user):
                    correct = msg.id == reaction.message.id and reaction.emoji in correctEmojis and user.id not in reacted
                    if (msg.id == reaction.message.id and user.id not in reacted):
                        reacted.append(user.id)
                    return correct

                reacted = []

                try:
                    answerEmoji, user = await self.bot.wait_for("reaction_add", timeout = time, check = check)

                    if (user.mention not in scores):
                        scores[user.mention] = 1
                    else:
                        scores[user.mention] += 1

                    embed.add_field(name = "Winner", value = user.mention)
                        
                except asyncio.TimeoutError:
                    pass

            elif (mode == "a"):
                await asyncio.sleep(time)

                gained = []
                lost = []

                for reaction in (await ctx.fetch_message(msg.id)).reactions:
                    correct = reaction.emoji in correctEmojis
                    for user in await reaction.users().flatten():
                        if (user.id == self.bot.user.id):
                            continue
                        if (user.mention not in lost):
                            if (user.mention in gained):
                                if (user.mention in scores and scores[user.mention] > 0):
                                    scores[user.mention] -= 1
                                gained.remove(user.mention)
                                lost.append(user.mention)

                            elif (correct):
                                if (user.mention in scores):
                                    scores[user.mention] += 1
                                else:
                                    scores[user.mention] = 1
                                gained.append(user.mention)

                            else:
                                lost.append(user.mention)


                embed.add_field(name = "Winners", value = "{} ({}%)".format(len(gained), 100*len(gained)/max(1, len(gained)+len(lost))))

            embed.add_field(name = "Correct Answers", value = "\n".join([answer[0] for answer in answerData if answer[2]]))
            await msg.edit(embed = embed)

            await asyncio.sleep(gap)

        await msg.clear_reactions()

        return scores, len(questionData)

    @commands.command(
        name = "quizhelp",
        aliases = ["qh"],

        hidden = True,
    )
    async def quizHelp(self, ctx):

        embed = discord.Embed(
            title = "Quiz Parameters",
            description = "Use these by adding a hyphen followed by the parameter to add. e.g\nquiz [name] -accuracy -time 30\nUse .quizlist for a list of available quizzes",
            colour = ctx.guild.get_member(self.bot.user.id).colour,
            timestamp = datetime.now(),
        )
        embed.add_field(
            name = "Mode (Max 1, Default: speed)",
            value = "**speed** - The first person to react correctly wins the point. \n**accuracy** - Everyone who reacts correctly wins the point.",
            inline = False,
        )
        embed.add_field(
            name = "Other",
            value = "**random** - Randomises the order of questions and answers. (Default: False)\n**time <seconds>** - The maximum time people have to answer in seconds. (Default: 30)\n**gap <seconds>** - The time between the end of one question and the start of the next one. (Default: 10)",
            inline = False,
        )
        await ctx.send(embed = embed)
        
    @commands.command(
        name = "quizlist",
        aliases = ["ql"],

        hidden = True,
    )
    async def quizList(self, ctx):

        availableQuizzes = self.executeSQL("""
            SELECT DISTINCT quizzes.name FROM quizzes
            INNER JOIN questions ON quizzes.id = questions.quiz
            INNER JOIN answers ON questions.id = answers.question
            WHERE quizzes.server = ? AND answers.correct = 1
        """, (ctx.guild.id,))

        embed = discord.Embed(
            title = "Available Quizzes",
            description = "\n".join([quiz[0] for quiz in availableQuizzes])
        )
        await ctx.send(embed = embed)

    def cog_unload(self):

        if (self.conn):
            self.conn.close()

