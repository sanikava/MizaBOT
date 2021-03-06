﻿import discord
from discord.ext import commands
import asyncio
import aiohttp
import random
from datetime import datetime, timedelta
import math
import json

# #####################################################################################
# math parser used by $calc
class Parser:
    def __init__(self, string, vars={}):
        self.string = string
        self.index = 0
        self.vars = {
            'pi' : 3.141592653589793,
            'e' : 2.718281828459045
            }
        for var in vars.keys():
            if self.vars.get(var) != None:
                raise Exception("Cannot redefine the value of {}".format(var))
            self.vars[var] = vars[var]
    
    def getValue(self):
        value = self.parseExpression()
        self.skipWhitespace()
        if self.hasNext():
            raise Exception("Unexpected character found: '{}' at index {}".format(self.peek(), self.index))
        return value
    
    def peek(self):
        return self.string[self.index:self.index + 1]
    
    def hasNext(self):
        return self.index < len(self.string)
    
    def skipWhitespace(self):
        while self.hasNext():
            if self.peek() in ' \t\n\r':
                self.index += 1
            else:
                return
    
    def parseExpression(self):
        return self.parseAddition()
    
    def parseAddition(self):
        values = [self.parseMultiplication()]
        while True:
            self.skipWhitespace()
            char = self.peek()
            if char == '+':
                self.index += 1
                values.append(self.parseMultiplication())
            elif char == '-':
                self.index += 1
                values.append(-1 * self.parseMultiplication())
            else:
                break
        return sum(values)
    
    def parseMultiplication(self):
        values = [self.parseParenthesis()]
        while True:
            self.skipWhitespace()
            char = self.peek()
            if char == '*' or char == 'x':
                self.index += 1
                values.append(self.parseParenthesis())
            elif char == '/':
                div_index = self.index
                self.index += 1
                denominator = self.parseParenthesis()
                if denominator == 0:
                    raise Exception("Division by 0 (occured at index {})".format(div_index))
                values.append(1.0 / denominator)
            elif char == '%': # hack
                div_index = self.index
                self.index += 1
                denominator = self.parseParenthesis()
                if denominator == 0:
                    raise Exception("Division by 0 (occured at index {})".format(div_index))
                values[-1] = values[-1] % denominator
            elif char == '^': # hack
                self.index += 1
                exponent = self.parseParenthesis()
                values[-1] = values[-1] ** exponent
            elif char == '!': # hack
                self.index += 1
                values[-1] = math.factorial(values[-1])
            else:
                break
        value = 1.0
        for factor in values:
            value *= factor
        return value
    
    def parseParenthesis(self):
        self.skipWhitespace()
        char = self.peek()
        if char == '(':
            self.index += 1
            value = self.parseExpression()
            self.skipWhitespace()
            if self.peek() != ')':
                raise Exception("No closing parenthesis found at character {}".format(self.index))
            self.index += 1
            return value
        else:
            return self.parseNegative()
    
    def parseNegative(self):
        self.skipWhitespace()
        char = self.peek()
        if char == '-':
            self.index += 1
            return -1 * self.parseParenthesis()
        else:
            return self.parseValue()
    
    def parseValue(self):
        self.skipWhitespace()
        char = self.peek()
        if char in '0123456789.':
            return self.parseNumber()
        else:
            return self.parseVariable()
    
    def parseVariable(self):
        self.skipWhitespace()
        var = ''
        while self.hasNext():
            char = self.peek()
            if char.lower() in '_abcdefghijklmnopqrstuvwxyz0123456789':
                var += char
                self.index += 1
            else:
                break
        
        value = self.vars.get(var, None)
        if value == None:
            raise Exception("Unrecognized variable: '{}'".format(var))
        return float(value)
    
    def parseNumber(self):
        self.skipWhitespace()
        strValue = ''
        decimal_found = False
        char = ''
        
        while self.hasNext():
            char = self.peek()            
            if char == '.':
                if decimal_found:
                    raise Exception("Found an extra period in a number at character {}".format(self.index))
                decimal_found = True
                strValue += '.'
            elif char in '0123456789':
                strValue += char
            else:
                break
            self.index += 1
        
        if len(strValue) == 0:
            if char == '':
                raise Exception("Unexpected end found")
            else:
                raise Exception("I was expecting to find a number at character {} but instead I found a '{}'".format(self.index, char))
        return float(strValue)
        
def evaluate(expression, vars={}):
    try:
        p = Parser(expression, vars)
        value = p.getValue()
    except Exception as ex:
        raise Exception(ex)
    
    # Return an integer type if the answer is an integer 
    if int(value) == value:
        return int(value)
    
    # If Python made some silly precision error 
    # like x.99999999999996, just return x + 1 as an integer 
    epsilon = 0.0000000001
    if int(value + epsilon) != int(value):
        return int(value + epsilon)
    elif int(value - epsilon) != int(value):
        return int(value)
    
    return value


# #####################################################################################
# Cogs
class General(commands.Cog):
    """General commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x8fe3e8

    def startTasks(self):
        self.bot.runTask('reminder', self.remindertask)

    async def remindertask(self):
        await self.bot.send('debug', embed=self.bot.buildEmbed(title="remindertask() started", timestamp=datetime.utcnow()))
        while True:
            if self.bot.exit_flag: return
            try:
                c = self.bot.getJST() + timedelta(seconds=30)
                for r in list(self.bot.reminders.keys()):
                    di = 0
                    u = self.bot.get_user(int(r))
                    if u is None: continue
                    while di < len(self.bot.reminders[r]):
                        if c > self.bot.reminders[r][di][0]:
                            try:
                                await u.send(embed=self.bot.buildEmbed(title="Reminder", description=self.bot.reminders[r][di][1]))
                            except Exception as e:
                                await self.bot.sendError('remindertask', "User: {}\nReminder: {}\nError: {}".format(u.name, self.bot.reminders[r][di][1], e))
                            self.bot.reminders[r].pop(di)
                            self.bot.savePending = True
                        else:
                            di += 1
                    if len(self.bot.reminders[r]) == 0:
                        self.bot.reminders.pop(r)
                        self.bot.savePending = True
            except asyncio.CancelledError:
                await self.bot.sendError('remindertask', 'cancelled')
                return
            except Exception as e:
                await self.bot.sendError('remindertask', str(e))
                await asyncio.sleep(200)
            await asyncio.sleep(40)

    def isDisabled(): # for decorators
        async def predicate(ctx):
            return False
        return commands.check(predicate)

    def isAuthorized(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isAuthorized(ctx)
        return commands.check(predicate)

    # get a 4chan thread
    async def get4chan(self, board : str, search : str): # be sure to not abuse it, you are not supposed to call the api more than once per second
        try:
            search = search.lower()
            url = 'http://a.4cdn.org/{}/catalog.json'.format(board) # board catalog url
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    if r.status == 200:
                        data = await r.json()
            threads = []
            for p in data:
                for t in p["threads"]:
                    try:
                        if t["sub"].lower().find(search) != -1 or t["com"].lower().find(search) != -1:
                            threads.append([t["no"], t["replies"]]) # store the thread ids matching our search word
                    except:
                        pass
            threads.sort(reverse=True)
            return threads
        except:
            return []

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isAuthorized()
    async def roll(self, ctx, dice : str = ""):
        """Rolls a dice in NdN format."""
        try:
            rolls, limit = map(int, dice.split('d'))
            result = ", ".join(str(random.randint(1, limit)) for r in range(rolls))
            await ctx.send(embed=self.bot.buildEmbed(title="{}'s dice Roll(s)".format(ctx.message.author.display_name), description=result, color=self.color))
        except:
            await ctx.send(embed=self.bot.buildEmbed(title="Format has to be in NdN", footer="example: roll 2d6", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['choice'])
    @isAuthorized()
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def choose(self, ctx, *choices : str ):
        """Chooses between multiple choices.
        Use quotes if one of your choices contains spaces.
        Example: $choose "I'm Alice" Bob"""
        try:
            await ctx.send(embed=self.bot.buildEmbed(title="{}, I choose".format(ctx.message.author.display_name), description=random.choice(choices), color=self.color))
        except:
            await ctx.send(embed=self.bot.buildEmbed(title="Give me a list of something to choose from 😔", footer="Use quotes \" if a choice contains spaces", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['math'])
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def calc(self, ctx, *terms : str):
        """Process a mathematical expression
        You can define a variable by separating using a comma.
        Example: (a + b) / c, a = 1, b=2,c = 3"""
        try:
            m = " ".join(terms).split(",")
            d = {}
            for i in range(1, len(m)): # process the variables if any
                x = m[i].replace(" ", "").split("=")
                if len(x) == 2: d[x[0]] = float(x[1])
                else: raise Exception('')
            await ctx.send(embed=self.bot.buildEmbed(title="Calculator 🤓", description="{} = {}".format(m[0], evaluate(m[0], d)), color=self.color))
        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="{} Error, use the help for details".format(self.bot.getEmote('kmr')), footer=str(e), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def jst(self, ctx):
        """Post the current time, JST timezone"""
        await ctx.send(embed=self.bot.buildEmbed(title="{} {:%Y/%m/%d %H:%M} JST".format(self.bot.getEmote('clock'), self.bot.getJST()), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isAuthorized()
    async def roleStats(self, ctx, *name : str):
        """Search how many users have a matching role
        use quotes if your match contain spaces
        add 'exact' at the end to force an exact match"""
        g = ctx.author.guild
        i = 0
        if len(name) > 0 and name[-1] == "exact":
            exact = True
            name = name[:-1]
        else:
            exact = False
        name = ' '.join(name)
        for member in g.members:
            for r in member.roles:
                if r.name == name or (exact == False and r.name.lower().find(name.lower()) != -1):
                    i += 1
        if exact != "exact":
            await ctx.send(embed=self.bot.buildEmbed(title="Roles containing: {}".format(name), description="{} user(s)".format(i), thumbnail=g.icon_url, footer="on server {}".format(g.name), color=self.color))
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="Roles matching: {}".format(name), description="{} user(s)".format(i), thumbnail=g.icon_url, footer="on server {}".format(g.name), color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['hgg2d'])
    @commands.cooldown(1, 10, commands.BucketType.default)
    async def hgg(self, ctx):
        """Post the latest /hgg2d/ threads"""
        if not ctx.channel.is_nsfw():
            await ctx.send(embed=self.bot.buildEmbed(title=':underage: NSFW channels only'))
            return
        threads = await self.get4chan('vg', '/hgg2d/')
        if len(threads) > 0:
            msg = ""
            for t in threads:
                msg += '🔞 https://boards.4channel.org/vg/thread/{} ▫️ *{} replies*\n'.format(t[0], t[1])
            await ctx.send(embed=self.bot.buildEmbed(title="/hgg2d/ latest thread(s)", description=msg, footer="Good fap, fellow 4channeler", color=self.color))
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="/hgg2d/ Error", description="I couldn't find a single /hgg2d/ thread 😔", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['thread'])
    @commands.cooldown(1, 3, commands.BucketType.default)
    async def gbfg(self, ctx):
        """Post the latest /gbfg/ threads"""
        threads = await self.get4chan('vg', '/gbfg/')
        if len(threads) > 0:
            msg = ""
            for t in threads:
                msg += ':poop: https://boards.4channel.org/vg/thread/{} ▫️ *{} replies*\n'.format(t[0], t[1])
            await ctx.send(embed=self.bot.buildEmbed(title="/gbfg/ latest thread(s)", description=msg, footer="Have fun, fellow 4channeler", color=self.color))
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="/gbfg/ Error", description="I couldn't find a single /gbfg/ thread 😔", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, name='4chan')
    @commands.cooldown(1, 3, commands.BucketType.default)
    async def _4chan(self, ctx, board : str, *, term : str):
        """Search 4chan threads"""
        nsfw = ['b', 'r9k', 'pol', 'bant', 'soc', 's4s', 's', 'hc', 'hm', 'h', 'e', 'u', 'd', 'y', 't', 'hr', 'gif', 'aco', 'r']
        board = board.lower()
        if board in nsfw and not ctx.channel.is_nsfw():
            await ctx.send(embed=self.bot.buildEmbed(title=":underage: The board `{}` is restricted to NSFW channels".format(board)))
            return
        threads = await self.get4chan(board, term)
        if len(threads) > 0:
            msg = ""
            for t in threads:
                msg += ':four_leaf_clover: https://boards.4channel.org/{}/thread/{} ▫️ *{} replies*\n'.format(board, t[0], t[1])
            await ctx.send(embed=self.bot.buildEmbed(title="4chan Search result", description=msg, footer="Have fun, fellow 4channeler", color=self.color))
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="4chan Search result", description="No matching threads found", color=self.color))


    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['reminder'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def remind(self, ctx, duration : str, *, msg : str):
        """Remind you of something at the specified time (±30 seconds precision)
        <duration> format: XdXhXmXs for day, hour, minute, second, each are optionals"""
        id = str(ctx.author.id)
        if id not in self.bot.reminders:
            self.bot.reminders[id] = []
        if len(self.bot.reminders[id]) >= 5 and ctx.author.id != self.bot.ids.get('owner', -1):
            await ctx.send(embed=self.bot.buildEmbed(title="Reminder Error", description="Sorry, I'm limited to 5 reminders per user 🙇", color=self.color))
            return
        try:
            d = self.bot.makeTimedelta(duration)
            if d is None: raise Exception()
        except:
            await ctx.send(embed=self.bot.buildEmbed(title="Reminder Error", description="Invalid duration string `{}`, format is `NdNhNm`".format(duration), color=self.color))
            return
        if msg == "":
            await ctx.send(embed=self.bot.buildEmbed(title="Reminder Error", description="Tell me what I'm supposed to remind you 🤔", color=self.color))
            return
        if len(msg) > 200:
            await ctx.send(embed=self.bot.buildEmbed(title="Reminder Error", description="Reminders are limited to 200 characters", color=self.color))
            return
        try:
            self.bot.reminders[id].append([datetime.utcnow().replace(microsecond=0) + timedelta(seconds=32400) + d, msg]) # keep JST
            self.bot.savePending = True
            await ctx.message.add_reaction('✅') # white check mark
        except:
            await ctx.send(embed=self.bot.buildEmbed(title="Reminder Error", footer="I have no clues about what went wrong", color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['rl', 'reminderlist'])
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def remindlist(self, ctx):
        """Post your current list of reminders"""
        id = str(ctx.author.id)
        if id not in self.bot.reminders or len(self.bot.reminders[id]) == 0:
            await ctx.send(embed=self.bot.buildEmbed(title="Reminder Error", description="You don't have any reminders", color=self.color))
        else:
            embed = discord.Embed(title="{}'s Reminder List".format(ctx.author.display_name), color=random.randint(0, 16777216)) # random color
            embed.set_thumbnail(url=ctx.author.avatar_url)
            for i in range(0, len(self.bot.reminders[id])):
                embed.add_field(name="#{} ▫️ {:%Y/%m/%d %H:%M} JST".format(i, self.bot.reminders[id][i][0]), value=self.bot.reminders[id][i][1], inline=False)
            await ctx.send(embed=embed)

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['rd', 'reminderdel'])
    @commands.cooldown(2, 3, commands.BucketType.user)
    async def reminddel(self, ctx, rid : int):
        """Delete one of your reminders"""
        id = str(ctx.author.id)
        if id not in self.bot.reminders or len(self.bot.reminders[id]) == 0:
            await ctx.send(embed=self.bot.buildEmbed(title="Reminder Error", description="You don't have any reminders", color=self.color))
        else:
            if rid < 0 or rid >= len(self.bot.reminders[id]):
                await ctx.send(embed=self.bot.buildEmbed(title="Reminder Error", description="Invalid id `{}`".format(rid), color=self.color))
            else:
                self.bot.reminders[id].pop(rid)
                if len(self.bot.reminders[id]) == 0:
                    self.bot.reminders.pop(id)
                self.bot.savePending = True
                await ctx.message.add_reaction('✅') # white check mark