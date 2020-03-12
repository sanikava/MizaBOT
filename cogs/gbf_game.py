﻿import discord
from discord.ext import commands
import asyncio
import random
from datetime import datetime, timedelta
import math
from operator import itemgetter

class GBF_Game(commands.Cog):
    """GBF related commands."""
    def __init__(self, bot):
        self.bot = bot
        self.color = 0xfce746
        # /gbfg/ game
        self.pitroulettestate = False
        self.pitroulettevictim = []
        self.pitroulettelist = []
        self.pitroulettecount = 0
        self.pitroulettemax = 0

    def startTasks(self):
        self.bot.setOnMessageCallback('pitroulette', self.pitroulette_callback, True)
        self.bot.runTask('cleanroll', self.cleanrolltask)

    async def cleanrolltask(self): # silent task
        await asyncio.sleep(3600)
        if self.bot.exit_flag: return
        try:
            c = datetime.utcnow()
            change = False
            for id in list(self.bot.spark[0].keys()):
                if len(self.bot.spark[0][id]) == 3: # backward compatibility
                    self.bot.spark[0][id].append(c)
                    change = True
                else:
                    d = c - self.bot.spark[0][id][3]
                    if d.days >= 30:
                        del self.bot.spark[0][id]
                        change = True
            if change: self.bot.savePending = True
        except asyncio.CancelledError:
            await self.bot.sendError('cleanrolltask', 'cancelled')
            return
        except Exception as e:
            await self.bot.sendError('cleanrolltask', str(e))

    def isDisabled(): # for decorators
        async def predicate(ctx):
            return False
        return commands.check(predicate)

    def isAuthorized(): # for decorators
        async def predicate(ctx):
            return ctx.bot.isAuthorized(ctx)
        return commands.check(predicate)

    def isGBFGgeneralAndMod(): # for decorators
        async def predicate(ctx):
            return (ctx.channel.id == ctx.bot.ids['gbfg_general'] and ctx.author.guild_permissions.manage_messages)
        return commands.check(predicate)

    # used by the gacha games
    def getRoll(self, ssr, sr_mode = False):
        d = random.randint(1, 10000)
        if d < ssr: return 0
        elif (not sr_mode and d < 1500 + ssr) or sr_mode: return 1
        return 2

    legfestWord = {"double", "x2", "legfest", "flashfest", "flash", "leg", "gala", "2"}
    def isLegfest(self, word):
        if word.lower() in self.legfestWord: return 2 # 2 because the rates are doubled
        return 1

    def tenDraws(self, rate, draw, mode = 0):
        result = [0, 0, 0]
        x = 0
        while mode > 0 or (mode == 0 and x < draw):
            i = 0
            while i < 10:
                r = self.getRoll(rate, i == 9)
                result[r] += 1
                i += 1
            if mode == 1 and result[0] > 0: break # gachapin / mukku
            elif mode == 2 and result[0] >= 5: break # super mukku
            x += 1
        return result

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['1'])
    @isAuthorized()
    @commands.cooldown(60, 60, commands.BucketType.guild)
    async def single(self, ctx, double : str = ""):
        """Do a single roll
        6% keywords: "double", "x2", "legfest", "flashfest", "flash", "leg", "gala", "2"."""
        l = self.isLegfest(double)
        if l == 2: footer = "6% SSR rate"
        else: footer = "3% SSR rate"
        r = self.getRoll(300*l)

        if r == 0: msg = "Luckshitter! It's a {}".format(self.bot.getEmote('SSR'))
        elif r == 1: msg = "It's a {}".format(self.bot.getEmote('SR'))
        else: msg = "It's a {}, too bad!".format(self.bot.getEmote('R'))

        await ctx.send(embed=self.bot.buildEmbed(title="{} did a single roll".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url, footer=footer))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['10'])
    @isAuthorized()
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def ten(self, ctx, double : str = ""):
        """Do ten gacha rolls
        6% keywords: "double", "x2", "legfest", "flashfest", "flash", "leg", "gala", "2"."""
        l = self.isLegfest(double)
        if l == 2: footer = "6% SSR rate"
        else: footer = "3% SSR rate"
        msg = ""
        i = 0
        while i < 10:
            r = self.getRoll(300*l, i == 9)
            if i == 5: msg += '\n'
            if r == 0: msg += '{}'.format(self.bot.getEmote('SSR'))
            elif r == 1: msg += '{}'.format(self.bot.getEmote('SR'))
            else: msg += '{}'.format(self.bot.getEmote('R'))
            i += 1

        await ctx.send(embed=self.bot.buildEmbed(title="{} did ten rolls".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url, footer=footer))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['300'])
    @isAuthorized()
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def spark(self, ctx, double : str = ""):
        """Do thirty times ten gacha rolls
        6% keywords: "double", "x2", "legfest", "flashfest", "flash", "leg", "gala", "2"."""
        l = self.isLegfest(double)
        if l == 2: footer = "6% SSR rate"
        else: footer = "3% SSR rate"
        result = self.tenDraws(300*l, 30)
        msg = "{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n".format(result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/300)

        await ctx.send(embed=self.bot.buildEmbed(title="{} sparked".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url, footer=footer))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['frenzy'])
    @isAuthorized()
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def gachapin(self, ctx, double : str = ""):
        """Do ten rolls until you get a ssr
        6% keywords: "double", "x2", "legfest", "flashfest", "flash", "leg", "gala", "2"."""
        l = self.isLegfest(double)
        if l == 2: footer = "6% SSR rate"
        else: footer = "3% SSR rate"
        result = self.tenDraws(300*l, 0, 1)
        count = result[0]+result[1]+result[2]
        msg = "Gachapin stopped after **{}** rolls\n{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n".format(count, result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/count)

        await ctx.send(embed=self.bot.buildEmbed(title="{} rolled the Gachapin".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url, footer=footer))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['mook'])
    @isAuthorized()
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def mukku(self, ctx, super : str = ""):
        """Do ten rolls until you get a ssr, 9% ssr rate
        You can add "super" for a 9% rate and 5 ssr mukku"""
        if super.lower() == "super":
            footer = "Super Mukku ▫️ 15% SSR Rate and at least 5 SSRs"
            result = self.tenDraws(1500, 0, 2)
        else:
            footer = "9% SSR rate"
            result = self.tenDraws(900, 0, 1)
        count = result[0]+result[1]+result[2]
        msg = "Mukku stopped after **{}** rolls\n{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n".format(count, result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/count)

        await ctx.send(embed=self.bot.buildEmbed(title="{} rolled the Mukku".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url, footer=footer))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def scratch(self, ctx):
        """Imitate the GBF scratch game"""
        # loot table
        loot = [
            ['Siero Ticket', 'Sunlight Stone', 'Gold Brick', 'Damascus Ingot'],
            ['Agni', 'Varuna', 'Titan', 'Zephyrus', 'Zeus', 'Hades', 'Shiva', 'Europa', 'Godsworn Alexiel', 'Grimnir', 'Lucifer', 'Bahamut', 'Michael', 'Gabriel', 'Uriel', 'Raphael', 'Metatron', 'Sariel', 'Murgleis', 'Benedia', 'Gambanteinn', 'Love Eternal', 'AK-4A', 'Reunion', 'Ichigo-Hitofuri', 'Taisai Spirit Bow', 'Unheil', 'Sky Ace', 'Ivory Ark', 'Blutgang', 'Eden', 'Parazonium', 'Ixaba', 'Blue Sphere', 'Certificus', 'Fallen Sword', 'Mirror-Blade Shard', 'Galilei\'s Insight', 'Purifying Thunderbolt', 'Vortex of the Void', 'Sacred Standard', 'Bab-el-Mandeb', 'Cute Ribbon'],
            ['Crystals x3000', 'Intricacy Ring', 'Lineage Ring x2', 'Gold Spellbook', 'Moonlight Stone', 'Gold Moon x2', 'Ultima Unit x3', 'Silver Centrum x5', 'Primeval Horn x3', 'Horn of Bahamut x4'],
            ['Coronation Ring x3', 'Legendary Merit x5', 'Steel Brick', 'Silver Moon x5', 'Bronze Moon x10', 'Half Elixir x100', 'Soul Berry x300']
        ]
        message = None
        # select the loot
        n = random.randint(4, 6)
        selected = {}
        selected[random.choice(loot[3])] = 0
        selected[random.choice(loot[0]+loot[1]+loot[2])] = 0
        for i in range(2, n):
            r = random.randint(1, 100)
            if r == 1: table = loot[0]
            elif r <= 4: table = loot[1]
            elif r <= 20: table = loot[2]
            else: table = loot[3]
            while True:
                x = random.choice(table)
                if x not in selected:
                    selected[x] = 0
                    break

        # build the scratch grid
        hidden = "???????????????"
        grid = []
        win = ""
        keys = list(selected.keys())
        while len(grid) < 9:
            x = random.choice(keys)
            if selected[x] < 2:
                selected[x] += 1
                grid.append([x, False])
            elif selected[x] == 2:
                if win == "":
                    win = x
                    selected[x] += 1
                    grid.append([x, False])

        # print the game
        win_flag = False
        reveal_count = 0
        fields = [{'name': "{}".format(self.bot.getEmote('1')), 'value':''}, {'name': "{}".format(self.bot.getEmote('2')), 'value':''}, {'name': "{}".format(self.bot.getEmote('3')), 'value':''}]
        pulled = {}
        msg = ""
        while True:
            # print the grid
            for i in range(0, 9):
                if i < 3: fields[i]['value'] = ''
                if grid[i][1] == False: fields[i%3]['value'] += "{}\n".format(hidden)
                else:
                    c = pulled[grid[i][0]]
                    if c == 3: fields[i%3]['value'] += "***{}***\n".format(grid[i][0])
                    elif c == 2: fields[i%3]['value'] += "**{}**\n".format(grid[i][0])
                    else: fields[i%3]['value'] += "{}\n".format(grid[i][0])
            # send the message
            if message is None:
                message = await ctx.send(embed=self.bot.buildEmbed(author={'name':"{} is scratching...".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, inline=True, fields=fields, color=self.color))
            else:
                await message.edit(embed=self.bot.buildEmbed(author={'name':"{} is scratching...".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, inline=True, fields=fields, color=self.color))
            await asyncio.sleep(1)
            # win sequence
            if win_flag:
                if win == "":
                    keys = list(pulled.keys())
                    while win == "":
                        i = random.choice(keys)
                        if pulled[i] == 2:
                            win = i
                    msg += "*The Final scratch...*\n"
                    await message.edit(embed=self.bot.buildEmbed(author={'name':"{} is scratching...".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, inline=True, fields=fields, color=self.color))
                    await asyncio.sleep(2)
                msg += ":confetti_ball: :tada: **{}** :tada: :confetti_ball:".format(win)
                for i in range(0, 9):
                    if i < 3: fields[i%3]['value'] = ''
                    c = pulled.get(grid[i][0], 0)
                    if grid[i][1] == False: fields[i%3]['value'] += "~~{}~~\n".format(grid[i][0])
                    elif c == 3: fields[i%3]['value'] += "**{}**\n".format(grid[i][0])
                    elif c == 2: fields[i%3]['value'] += "__{}__\n".format(grid[i][0])
                    else: fields[i%3]['value'] += "{}\n".format(grid[i][0])
                await message.edit(embed=self.bot.buildEmbed(author={'name':"{} is scratching...".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, inline=True, fields=fields, color=self.color))
                break
            # next pull
            i = random.randint(0, 8)
            while grid[i][1] == True:
                i = random.randint(0, 8)
            grid[i][1] = True
            reveal_count += 1
            selected[grid[i][0]] -= 1
            pulled[grid[i][0]] = pulled.get(grid[i][0], 0) + 1
            if reveal_count == 9 or (selected[grid[i][0]] == 0 and grid[i][0] == win):
                win_flag = True

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 180, commands.BucketType.user)
    async def roulette(self, ctx, double : str = ""):
        """Imitate the GBF roulette
        6% keywords: "double", "x2", "legfest", "flashfest", "flash", "leg", "gala", "2"."""
        l = self.isLegfest(double)
        if l == 2: footer = "6% SSR rate"
        else: footer = "3% SSR rate"
        mode = 0
        roll = 0
        rps = ['rock', 'paper', 'scissor']
        d = random.randint(1, 36000)
        ct = self.bot.getJST()
        fix200S = ct.replace(year=2020, month=3, day=29, hour=18, minute=0, second=0, microsecond=0)
        fix200E = fix200S.replace(day=31, hour=5)
        if ct >= fix200S and ct < fix200E:
            msg = "{} {} :confetti_ball: :tada: Guaranteed **1 0 0 R O L L S** :tada: :confetti_ball: {} {}".format(self.bot.getEmote('crystal'), self.bot.getEmote('crystal'), self.bot.getEmote('crystal'), self.bot.getEmote('crystal'))
            roll = 10
            d = 0
            if l == 2: footer = "3% SSR rate ▪️ You won't get legfest rates, you fool"
            else: footer = "3% SSR rate"
            l = 1
            mode = 3
        elif d < 300:
            msg = "{} {} :confetti_ball: :tada: **2 0 0 R O L L S** :tada: :confetti_ball: {} {}".format(self.bot.getEmote('crystal'), self.bot.getEmote('crystal'), self.bot.getEmote('crystal'), self.bot.getEmote('crystal'))
            roll = 20
        elif d < 1500:
            msg = "**Gachapin Frenzy** :four_leaf_clover:"
            mode = 1
        elif d < 2000:
            msg = ":confetti_ball: :tada: **100** rolls!! :tada: :confetti_ball:"
            roll = 10
        elif d < 6200:
            msg = "**30** rolls! :clap:"
            roll = 3
        elif d < 18000:
            msg = "**20** rolls :open_mouth:"
            roll = 2
        else:
            msg = "**10** rolls :pensive:"
            roll = 1
        # janken
        """if d >= 2000 and random.randint(0, 2) > 0:
            a = 0
            b = 0
            while a == b:
                a = random.randint(0, 2)
                b = random.randint(0, 2)
            msg += "\nYou got **{}**, Gachapin got **{}**".format(rps[a], rps[b])
            if (a == 1 and b == 0) or (a == 2 and b == 1) or (a == 0 and b == 2):
                msg += " :thumbsup:\nYou **won** rock paper scissor, your rolls are **doubled** :confetti_ball:"
                roll = roll * 2
            else:
                msg += " :pensive:"
        """
        # rolls
        if mode == 0 or mode == 3:
            result = self.tenDraws(300*l, roll)
            msg += "\n{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n".format(result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/(roll*10))
        elif mode == 1:
            result = self.tenDraws(300*l, 0, 1)
            count = result[0]+result[1]+result[2]
            msg += "\nGachapin stopped after **{}** rolls\n{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n".format(count, result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/count)
            if count == 10 and random.randint(1, 100) < 99: mode = 2
            elif count == 20 and random.randint(1, 100) < 60: mode = 2
            elif count == 30 and random.randint(1, 100) < 30: mode = 2

        if mode == 2:
            result = self.tenDraws(900, 0, 1)
            count = result[0]+result[1]+result[2]
            msg += "\n:confetti_ball: Mukku stopped after **{}** rolls\n{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n".format(count, result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/count)

        if mode == 3:
            result = self.tenDraws(1500, 0, 2)
            count = result[0]+result[1]+result[2]
            msg += "\n:confetti_ball: :confetti_ball: **Super Mukku** stopped after **{}** rolls :confetti_ball: :confetti_ball:\n{} {} ▫️ {} {} ▫️ {} {}\n**{:.2f}%** SSR rate\n".format(count, result[0], self.bot.getEmote('SSR'), result[1], self.bot.getEmote('SR'), result[2], self.bot.getEmote('R'), 100*result[0]/count)

        await ctx.send(embed=self.bot.buildEmbed(author={'name':"{} spun the Roulette".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description=msg, color=self.color, footer=footer))
        #await ctx.send(embed=self.bot.buildEmbed(title="{} spun the Roulette".format(ctx.author.display_name), description=msg, color=self.color, thumbnail=ctx.author.avatar_url))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['setcrystal', 'setspark'])
    @isAuthorized()
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def setRoll(self, ctx, crystal : int, single : int = 0, ten : int = 0):
        """Set your roll count"""
        id = str(ctx.message.author.id)
        try:
            if crystal < 0 or single < 0 or ten < 0:
                raise Exception('Negative numbers')
            if crystal > 500000 or single > 1000 or ten > 100:
                raise Exception('Big numbers')
            if crystal + single + ten == 0: 
                if id in self.bot.spark[0]:
                    self.bot.spark[0].pop(id)
            else:
                self.bot.spark[0][id] = [crystal, single, ten, datetime.utcnow()]
            self.bot.savePending = True
            try:
                await self.bot.callCommand(ctx, 'seeRoll', 'GBF_Game')
            except Exception as e:
                await ctx.send(embed=self.bot.buildEmbed(title="Summary", description="**{}** crystal(s)\n**{}** single roll ticket(s)\n**{}** ten roll ticket(s)".format(crystal, single, ten), color=self.color))
                await self.bot.sendError('setRoll', str(e), 'B')
        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="Give me your number of crystals, single tickets and ten roll tickets, please", color=self.color, footer="setRoll <crystal> [single] [ten]"))
            await self.bot.sendError('setRoll', str(e), 'A')

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=['seecrystal', 'seespark'])
    @commands.cooldown(30, 30, commands.BucketType.guild)
    async def seeRoll(self, ctx, member : discord.Member = None):
        """Post your roll count"""
        if member is None: member = ctx.author
        id = str(member.id)
        try:
            # get the roll count
            if id in self.bot.spark[0]:
                s = self.bot.spark[0][id]
                if s[0] < 0 or s[1] < 0 or s[2] < 0:
                    raise Exception('Negative numbers')
                r = (s[0] / 300) + s[1] + s[2] * 10
                fr = math.floor(r)
                if len(s) > 3: timestamp = s[3]
                else: timestamp = None
            else:
                r = 0
                fr = 0
                timestamp = None

            # calculate estimation
            # note: those numbers are from my own experimentation
            month_min = [90, 80, 145, 95, 80, 85, 85, 120, 60, 70, 70, 145]
            month_max = [65, 50, 110, 70, 55, 65, 65, 80, 50, 55, 55, 110]
            month_day = [31.0, 28.25, 31.0, 30.0, 31.0, 30.0, 31.0, 31.0, 30.0, 31.0, 30.0, 31.0]

            # get current day
            if timestamp is None: now = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            else: now = timestamp.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            t_min = now
            t_max = now
            r_min = r % 300
            r_max = r_min
            while r_min < 300 or r_max < 300: # increase the date until we reach the 300 target for both estimation
                if r_min < 300:
                    m = (t_min.month-1) % 12
                    r_min += month_min[m] / month_day[m]
                    t_min += timedelta(days=1)
                if r_max < 300:
                    m = (t_max.month-1) % 12
                    r_max += month_max[m] / month_day[m]
                    t_max += timedelta(days=1)

            # roll count text
            title = "{} {} has {} roll".format(self.bot.getEmote('crystal'), member.display_name, fr)
            if fr != 1: title += "s"
            # flavor text
            if r >= 1200: description = "0̴̧̛͙̠͕͎̭͎̞͚̥̹̟̫̳̫̥͍͙̳̠͈̮̈̂͗̈́̾͐̉1̶̧̛̼͉̟̻̼͍̥̱͖̲̜̬̝̟̦̻̤͓̼̰̱͔̙͔̩̮̝̩̰̐̾͐͑̍̈́̈̋̒̊̔̿́͘͝ͅ0̶̨̢̢̢̨̧̨̡̧̛̛̱̲̫͕̘͍̟̞̬͍͇̜͓̹̹̗̤̗̖̻̞͈̩̪̗̬̖͍̙͙̗̩̳̩̫͕̥̘̩̲̲̩̈́̏̀̽͑̅̔̇̎͂͗̄̂̒̈̇̊̎̔͐̍̓̓̆͒͑̾̓̿̊̀̎̈́̓̂̉̎̉̋̆̇̆̍̈́͗͂̚͘͘͘̚̚̚͜͜͜͝͝͝ͅ1̷̢̧̫͖̤͉̞͓͖̱͎͔̮͔̺̺͈̜͔͇̦͍͓̲̩̼̺̹͙̪̺͉̰͚̺̗̹̝̥̱͍̥͚͓̲̻̣͈̣̥̆̑̋͒̆̆̒̐͑́̏̀̋̍̅͂̇͛̑́̏͑̑͛̈́̒͜͜͠͝͠͝ͅ0̸̧̧̻̦̱̳͖̝̣̻̩͒͂̓̒̈́̆̓̑̅̎͗̓͛͗̍̃̈́̒̈̄̄̚͠͝0̷̢̨̛͔͍̝͉̗͇̫͈̣̳̼͙͓̮̞̻̫̝͓̬̼̲̘̼̫̤͎͛̈̒͒̎͊̌̑̂̉̂̍͂̀̐̈́̓̓̃͊̈́̑̍͂̋̐͂̕͜͝͝1̵̢̡̡̧̡̨̘̖͓̭̩͍̦̭͍̭̙̜̝̙̹̰̻͖̳̱̫̦̙͓̙̺̮͈̳͇͍̹̗̬̖͇͉̳̃̏͗̉ͅ1̴̡̢̨̨̯̺͕̮͈͈̪̮̘̱͓̜̗͓͓͚͕̱̮̬͈̦̖͚̪̬̠͎̫̻̯̭̫̫̜̺̪̞̝̞͖͈͓̖͓̼̲̓̓̈̿̒̋̏̓͂̋̔̿̀̌̏̐̓͑̎̓͐̃̇͑͐̒̀̑͗̇̀̃͘͘̚͜͝ͅ0̷̨̡̡̧̨̛̣͕̖͎̱͚̦̯̻̳̠̞͇̙̣̜͎͍̬̹͖̟̖̠̘̪̞͓͖̫̣̹̫͓̯̖̯͓̻̯̘̫̣̤̤̝̘͙̣͇̯̥̓̒͐͂̄̈́̾͋͐̃̍͛̍͒̓̌̌̇̋͌͂̎̽̇́̈́̒̈́̑̿̈́̇͊̀̽̿͛́͆̊͒͒͊̀̄͌̈͑͂̄̏̿̕̚̕͘͜͠͝͠ͅ1̷̛͕͎̲̙̦͑̔̐̀̊́̊̾̊͂͊̎̀̂͊͐̍́̀̓̊͊̒͊̇̋̉̂̏͌̀̈̓̚͝ͅ1̵̡̡̡̨̧̢̳͉̺̯͓̗̞̺̯͔̯̫̠̮̭͉̗̬̝̜͙̥̠̝͈̯͍̜͉̪̺̘̈̌̏̆̄1̴̛̺̋̄͛̈́́̒̈́̊͂͊͆̍̇̔͊̐̎̇̆̃̈́̈́̌̉̈́̽͑́͑̆̋̀̽̍̎͛̿̊͊̊͛̄̄̓̌́̓́̿̓́̓͘̚̕͠͝͝͠0̸̛͓̑̍̊̒0̵̢̧̪͉̖͕͇̟͔̟͕͙̠͎̥̝̣̬͕͚̤̟͙̣̳̲͆̒͂͆̿̍̈́̕0̴̨̨̧̢̛͚̦̟̟̩̳̘̮͔̭̰̘̹̱͉͕̱̭̬̦̮͈̜̙̻̼̝͚̳͔͎͔͈̦͉̤͔͕͊̉̽̄̋͒͛͒̓̊̃̔͒͌͑̈́̆̅́̍͋̅̏̈́́͒̆̍̽͌́̕̚̕̚͜ͅ0̷̧̧̡̨̱̺̤̪̝͈̲̪̻̹̞̰̼̣̻̮̠͙͚̤̻͚̘̠͔͓͈͎̙͉̩̰͎͍̤̼̞̜̦̲͍̲̭͈̱̠͕̲̯͍͋̑̐̎̉̆̇̉̚͜͜͝ͅͅͅͅ0̶̡̲̼̦͎̬͚͉͓̻̝͙̪̪̫̭̥̰̺͈̜̝͖̭̰̤̈͂̈͌͊͛͆̔̓̉̍̍̇̃͂̇̔̿̾̒̆̓͊͊̑̍̅̔͆͝͝ͅ1̸̛̛̛̛̼͙͇̗͈͚̤̅͛͊̾͌̌̌̑̒̆̐̇̃̎̅̈́̂͋̽͗̀̐̎̒͊̏̿̓̐͆́̒̐̋̌̂͂̈̀̚͠͝1̷̡̨̧̢̡̨̝̟͚̜̞̻͙̳̻̣̱̗̬̠̘̤̪̮̻̟͔̺̥̳̯͔̲͈͉͇̥̼̘͖͉̼͙̠͓̘̯̱̜̗̼͓͓̳̠͊͌͌͛̌́̉̽̿͐̆͌̽̕͜ͅͅͅ0̴͙̩̤̳̼̼̰̲͍̝̳͎̭̙͓̙̱͉͚̯̌̋̐̒̒̍́́̏̍̈́͐̀͗̓͋̿̋̏0̵̡̧̡̢̨̣̻͖̹͕̬͉̟̰̱̬͙̪̬̰̫͖͚̩̪̘͖͓̫̣͉̮̲͎̘͓̗̥̦̞͇̖̦̩̼̮̝̙̈́͐̇̇̄̿̒̆̓̐̌̄̃̐͐̃͆̄̂̉͑͋̉͆͋̓͊̆͌̆̍̔̍͐̈́̾̓͋͗̀̈́͌̓͋̐̉͂͗̒̕̚͘͠͝͝0̸̧̢̨̡̨̧̛̖͙̰̮̙͉̬̬̪̟̮̣̫̳̭̤̞̖̩͔̰̣͇͓͓͋͂͂̄̉̀̊͂̌̍͋̒̋̋̓͂̽̌́̎̀̄̅̄̒̉͐̓͑͐̃̿̍̕̕͘͠ͅ0̸̡̢̡̧̛̪̫̺̪̩̜̜̼̘̺͚͉̩̮͍̜̪̪̪̰́̓͊̾̽̃̿̅͗̏̐̅͗̅͋̇̓̑͆͌͂̅̃͋͒̿̔͛̀̄̐͂͊̒̂͋̕̚͜͝͝͠1̷̛̛̛̫̙̝̺̹̜͕̮̺͈̏̽͛͒̃̈́͐̂̓̍͒́̑̃̒̒͋̅̐̋̌͗̎͒̓̊̉͒͒͗͋̓̓́̅̊̋̽̚͘͝͝͝͝͠0̸̧̨̢̡̧̡̧̛̼̦͓͔͍̠͇̯̘͓̮̼̠̼̫̝̮̪̹̘̘̗̬̫͍̺̭͈̜̲̭̳̜̹̖̩͋̓͋̈́́̈̍̇́͋̋̔̌̀̓̓͊͐̃̇̎́̋̈̀͛̎̒̏̊͂͗̕͝͝͝͝͠ͅ1̸̛̦̉̇̐̒̈͑̾̽͒̈̋̏̍̅̈̈́̊̂̾̀̕̚͘͘̕͝1̷̛̮̱͇̮̦̞̝̣͔̇́̍̔̄̀͂̏̿͗̎̚̕͘ͅͅ1̸̺̭̼̤̩̫̬̳͇̗̭̬̫̺͍̳̠͆̈́̔̓͋̄̈́̀̒̔̅͋̅̓̑̊͑̿̉͒͌̍̓̆͊́̚͝͝͝͝ͅ0̴̨̨̨̘̞͓̮̬̹̪͉̻͎͔̪̗͙̉̈̆̈͋͒̾̊͐̐͆̈̉̇̈́̏́̌͗̍̏̒̋̔͒͒͘̚̕͘͠͝ͅ0̴̡̧̛̭̘̞̹̮̼̼̥̫̯͚̮̙̮͓͚̝͇̆̓͂̇͂͒̆̒̂̀͆́̇̉̈́̐̀̿̌̎̿̃͛̊̄̑̃͛̍͂͒̚̚͜͜͠1̸̢̧̢̧̨̛̛̱̠̖̫̬̦̘͓͍̯̺̞͈̱̞͔̮̮̪͔͚̟̞̰̠̪͑̅̀̈́̀̈́͑̏̋̈́̂̓̄́͋̿͌̇͑̈̈͛̀̈͐̃̄͛́̊̌̂͋͒̉̀̀̍͆͒͆̈́͌̎̍̃͌͜͝͝͝͠ͅͅ0̸̻̺̱̦̖͈̯̼͙̳̤͉̬̫͖͚̲̝͖͈͉̼̺̲̬̣̘̦̺͈͕̈̅̌͂̋̋̏̀͒́͌̐̀̄͆͐̐̊́́̄́̓́̑̾͗̃͒̋̽̍̆̚̕͘͜͝͝͝ͅ0̶̨̧̨̡̗̣̬͍͈̱̣̭͉͌1̵̨̛̛̛̘͍̠̟̹͚̟͚̻͚͔̗̘̻̭͙͇̇̀͂̉̂͛̎̂́̽̒͗̑̾̊̅́͛͗̾͌̉͌́͌̔͆̊͆̍̊̔͂͑̓̊̓̋̿͌́̇̀̃́͆̐͗̿̋̑̓̚̕͜͝͝1̵̧̧̛̘͕̹̥͔̻͇͖̪̘̙̪̯̭̺͓͎̣̳̦̻̻͓͍͓̹̙̲̝̘̞̱̯̝̘̖͓̤̜̭͙͎̑̃̃̌͆̃͌̋͋̾͒̈́̎͌̈́͒̆̌͆̅̀̅͑̑̿͌̏̀̇͗̈́̚̕͜͠͝͝ͅ0̴̢̧̨̧̡̢̡̡̝̖̥̖̮̲͔͚̳͙̹̪̣̭̹̠̪̯͍͇̼͈̙̭͈̤̤̼̺̱̰̥̭̺͇̘̻͙̺̮̹͚̯̤̩̹̟̝̟́̔̊̀̊̽̓͜͜1̵̡̨̨̛̺͎̤̰̤͎̯̮͔͎͇̱̠̳͙̻̳̗̬͙̼̱͈̰͓͕͕͔͍̫̼̯͖̘͒̓̒͆̎̋̆͌͌̿̾̑̀̑̄͐̈́͑̒͗̔͋̾̿̐͑͂͊͐͆̿͑͐͗̐̑̈́̅́̍̋̎̃͂̌̃͘͘͘͘͘̕͠͠0̶̨̨̧̨̢̪͙̩̜̩̟͍̮̟̪̙͚̭̭͇̲̹̟̳͙͇̥̗̭̹̺̥͇̮̞͙̹͎̍̃̎̊̐̎͜͜͜1̸̡̨̡̢̢̧̨̠̝͉̤̹̺̠͕̹̬̝̳̟̦͙͕̯̦̟̰͚̹͙͔̫͖̹̪̙̪̞̖̠͔́͗̓͜ͅͅ1̸̢̨̛̛͍̣̠̠̭̯͈̱͕̘̼͖͖͇̠̰̟̙̪̪̳͙̞̭͉͙̓̔̈́͌͑̌͑̉̈́́͌̍̿̀͌͂̎͊̎̇̌̆̒͊͒͆͊̆́͐̕͘̕͝͠͠ :robot:\n"
            elif r >= 1150: description = "P̶̧̢̺̜̮̟̼͔͔̻̲̩͎̘̖̲̐͂̑͂͛́͑̍̊̓͌̀̃͛͊͑͋̑̽̀́̆̀̔͋̋̂̏͒̀̎̈̾͑̉̅͒̉͂̑͒̕̕̚̚͝͝͝͝͝͝͝ļ̴̡̩͓͙̪̫̥͇͈͈̪̭̣̲͇̥̪͍̫̼̟͙̱̟̤̩̬͇̬̝͇̞͆͆͆̓̾̎͌̈͆̾̅̀͐̄̇̈́̔̊́̾̈͗̊̏̊̀̀̕̚̕͜͝͝ͅe̵̡̢̨̢̨̧̨̛̛̗̪̟̼̘̤̻̭̮̙̼̞͙̲̗̟͔̠̲̦̯̖̪̪͖̱̳̼̺͎͎̬̜̤̣͍̩̫̱̪̮̰̗̲̫̾̀̀̍̈́͂͋̑͑̑͒̈́̊͊̑́̐̅̿̈́̎͗̀̔̍̔̋̍̄͊̑̆̀̏̏̈́̀̉̈̐̅̚͘͘͜͜͝͝ͅͅȧ̴̢̢̧̧̢̡̳͕̲͖̰͔̝͖̱̙͙̫̞͕̮̫̼̤̹͔̫̹͉͚̞̠̬͎̘̯̱̳̯̠̪̰͎̖̻̹̖̜̪̣͍͋̄̐̍̽̒̓̀̐̈́̚͜ͅͅs̷̢̨̡̡̢̛̛̙̫̮͙̤͎̗̭̯̭͚̖͕̰̜̱̘̥̝͖̺͇̳̥̆͒̽͒̓̅̀́̽͌͌͌͂̉͛̊͌̌̉̌̋̈̀̽̍̀̔̋̀̒͒̃̌̊̆̍̀͊̐̐̇̑̽̊͘̕̕͝ͅe̶̢̧̨̢̧̨̝̗̝̠͙̳̼̙̤͍̠͖̙̖̱̳̼̘͉͍̲̦͉̝̞̞̬̮̝̱̥̪̟̯̹̹̘͇̗̯͓̬͖͐̓͛͛̓̌̂͊̚͘͠ͅ ̴̧̢̩̪̥̺̼͙̺̱̞̩̞͕͇̰͔̙͎͈̼̠̮͓̬̺͍̥͍͙̰̮̹̔̈͒̋͂͋̇̿̀̓̏̋̋̅̓͘̚͜͠͝͝Ş̵̛̛͇̙̟̼̤̫̱͖͖̮̩̹̭̮̣̩̫̙̳̗̜͓̪̻̖͇̼͖̣̝̈̏̏̈́̍̍̃̓̒̾̎͐͗͂̑͐͆̃͐̎̽͂͆͊̐̀̎̂͗̀́̿̎̆̀̾́̃̃̌̒̍̓͌̉̍̕͘̕͝͠͝ͅp̵̡̧̙͈̗̟͚̳̱͔̳̺̟̤̞̰̺̫̤͙̜̩͚̹̰͎͚͕̭͕̀̈̈̉̎̔̇ͅͅa̷̢̧̢̧̨̙͔͇͈̭̥̦͖̭̲͎̥͈͚͖̟͓̱͚͉̰̣͍͉̰͇͔̖̲̖͙̫̰̜̯̦͆̌̋̂̀̓͊́̓̄̒̈́̓͌̅́́̀͑́͊̚̕͜ͅŗ̵̡̗̲͇̺̰̭͕̪̩͋̊̎̔͒͛̈́̿͊͂̂̏̑́̉́͒͌̑̎͐͊̒͂́̄̋́͋͂̅̅͗͊̕̚͘̕̕̚͘͠͠ͅķ̵̨̧̧̹̩͇̣͔̤̦͍͉̘̘̹̹̠̪̰͉̗̯̦̣̘͉̳̦̼̥͕̣̪̭̩̦̥͓̝̣̰͉̻̇̈́̾̈͊̈́͗̈́̈́̌̂̈́͒̏̐͆̀̔̿̉̅̈́̀̈́͌̌̈͊̐̂͒̓́̀͛̌͘̚͘͘̚͘͜͜͝͝͠͠ :robot:\n"
            elif r >= 1100: description = "Į̵̨̡̧̧̢̧̧͈͍͓͎̻͓͚̼̭̬̺̠̺̘̰̬̖̥̘̪̞̠̟̦̪͕̺̙͍͈̭͚̫̤͕̪̖̩̲̜̈́̅̍͛̽̑̐͋̀̅͂̑͋̊͂̒̊̀̂͊̈́͆̃͌̂̆̓́̒̓̈̒̍̑̂̓̕͘͘̕̕̕͝͝ͅͅt̷̨͇̥͇̭̹̀̔́̉͗̃͂̀͗̐̐̈́̎̀͘͜ ̸̡̛̗̭̫̟̫̬͇̲̳̺̗̦̭̤̠̗͓̳̥͉̗̖̰͎̩̬͚̙̯͕̟̭̗̮̤̲̭̲͉̠̦̹͎̩̤̺̖͈̘̞͇͒̂͆͆͗̂͗͛̒̏͒́͛̏͂͋̿͊̽̊͊̂̋́̐͌̇̄͛̐̐̌͒̏̔̑́͐͐͘̕͜͜͝͝͝h̸̢̡͔̗͕̻͍͚̦̪͇̺̘̗̞̭͇̰̼̠̟͉̰̤̞̞͔͙̻̯̬̬̬͓̩̻͖̞͈̙̐̊̓͒̒́͊̓̆̀͑́̌̀̊̓̿̎͛̍̅̋̔́̆̓̎̊̊́̀̄̂̾̎̍̏̒͛̆̇̉͐̏̏̂̃̕̚͘̕̚͠͝ͅŭ̷̢̯̱̤͎̦̥̜͈̉̆̏̊̄̈́̾̍̇͗̈́̈́͑̑́͌́̊̂͂̈́̉̓̐̑̃̾̽̊̂̕̕͜͝͝͝r̴̡̢̫̪͎̜͉͕̹̼̞̭̥̖̼̤̻̥͈͇̓̓͊͂͑̐̉̂̍̈́̏̓͜͝ͅţ̵̛̩̮̝̼̲͚̩̼̖̫̖͔̪̘̫͍̗̭̦̪͒͐̆̔͛̋̑̒̄̓̏̃̎̓̈́͛̇͛͋͗̅̏̊́̿̐͐͌͑͐̎̏̀̏͐̔̊̎̆̽̓̀̄̌́͘͜͝͝͝ͅs̸̛͚̣͛̀́́̌͌̏͌̉̐̒͑͋̐̍̚̕͝ :robot:\n"
            elif r >= 1050: description = "S̷̨̧̢̯̝̱̩̥̺̹̜̬̳̜̳̞̪̳̘̼͓̭͖̮̱͈̼̫̰̘̟̻̞͈̩͔̻̯̥̜͔̭̰̾͌̌̊̍͊͛̊̉̀͛̑̍͆̂̐̔̈̍̅̎̐͊̐̓͂̀͒̾̑̄͗͛̄͊̑̿̿̉́̉̌͋̂̕͜͜͝͠ͅͅţ̸̢̨̢̨̨̳̳̮͉̰͖͈͓͈̖̗̻̭̺̳̮̜͕͕͚̜͎̳͇̹̪̪̯͓̤͔͖͇̣̼̬̺͙̞͉͋͊͐͆̽͜͜ơ̵̡̨̧̰̫͔͓̘̗̺͚̺͓̠̹̤̻̟͖̮͎͎̰̦̤̥̘̹̼̗̭͓̻͈͔̱̈́̔͒͗̈͒̈́͛̎̋͛̌̏͂͂̊͊͊̓̏̈́̑̆͗͊̄̎͒̌̎̈́̀̆͑̒̾͌͂́͌̽̋̕̚̚̕͠͝͝͝͝ṕ̶̨͈̜̰̓̾̏̍̐̊̾̃͑̏̂̐̽̔͋̽̀̈́̍̾͊̑̃̽́̈́̚͜͠͠͝ ̴̛͍͙̺̳͚̖͉̝̜̦̘̥̭̤̹̂̈́̌̀̂͌̑̔͊̅̾͗̊̈͝ņ̵̧̢̳̣̥̙̭̭̖̖̲͓̦̗̩̝͉̦̣͉̬̗̙̘̪̲͖̜̟̫͓̖̦̣̩̝͙̫͈́̋̽͂̓͐͌̀̂̌̑̏͌̍̑̿̒̌͗̽͆͐̈́̆̅̋̆̽̍̅̅̃̑̈́̍̃͘͜͜͝ͅö̵͈́w̷̧̧̧̢̛̛̗̺̪͍̬̪͚͇͇̯͈͓̰̯̻̭̹̺̞̣͍͇̯̪̮̬̙͓̤̱̘̱͓̫̅̈̓͛͗̋̐̓̑̎́̓͆͒͂́̈́̈́͗́̌̌͂͊̄̊̈́̋͌́̓̌̒̑̆̐́̐͛̆̈́̓̓̚̚͝͠͝͝͝͠͝ͅͅͅ :robot: \n"
            elif r >= 1000: description = "ReAcHiNg CrItIcAl :robot:\n"
            elif r >= 900: description = "Will you spark soon? :skull:\n"
            elif r >= 600: description = "**STOP HOARDING** :confounded:\n"
            elif r >= 350: description = "What are you waiting for? :thinking:\n"
            elif r >= 300: description = "Dickpick or e-sport pick? :smirk:\n"
            elif r >= 250: description = "Almost! :blush: \n"
            elif r >= 220: description = "One more month :thumbsup: \n"
            elif r >= 180: description = "You are getting close :ok_hand: \n"
            elif r >= 150: description = "Half-way done :relieved:\n"
            elif r >= 100: description = "Stay strong :wink:\n"
            elif r >= 50: description = "You better save these rolls :spy: \n"
            elif r >= 20: description = "Start saving **NOW** :rage:\n"
            else: description = "Pathetic :nauseated_face: \n"
            # estimation text
            footer = "Next spark between {}/{}/{} and {}/{}/{}".format(t_min.year, t_min.month, t_min.day, t_max.year, t_max.month, t_max.day)
            # sending
            await ctx.send(embed=self.bot.buildEmbed(title=title, description=description, footer=footer, timestamp=timestamp, color=self.color))
        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Error", description="I warned my owner", color=self.color, footer=str(e)))
            await self.bot.sendError('seeRoll', str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True, aliases=["sparkranking", "hoarders"])
    @isAuthorized()
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def rollRanking(self, ctx):
        """Show the ranking of everyone saving for a spark in the server
        You must use $setRoll to set/update your roll count"""
        try:
            ranking = {}
            guild = ctx.message.author.guild
            for m in guild.members:
                id = str(m.id)
                if id in self.bot.spark[0]:
                    if id in self.bot.spark[1]:
                        continue
                    s = self.bot.spark[0][id]
                    if s[0] < 0 or s[1] < 0 or s[2] < 0:
                        continue
                    r = (s[0] / 300) + s[1] + s[2] * 10
                    if r > 1000:
                        continue
                    ranking[id] = r
            if len(ranking) == 0:
                await ctx.send(embed=self.bot.buildEmbed(title="The ranking of this server is empty"))
                return
            ar = -1
            i = 0
            emotes = {0:self.bot.getEmote('SSR'), 1:self.bot.getEmote('SR'), 2:self.bot.getEmote('R')}
            msg = ""
            top = 15
            for key, value in sorted(ranking.items(), key = itemgetter(1), reverse = True):
                if i < top:
                    fr = math.floor(value)
                    msg += "**#{:<2}{} {}** with {} roll".format(i+1, emotes.pop(i, "▫️"), guild.get_member(int(key)).display_name, fr)
                    if fr != 1: msg += "s"
                    msg += "\n"
                if key == str(ctx.message.author.id):
                    ar = i
                    if i >= top: break
                i += 1
                if i >= 100:
                    break
            if ar >= top: footer = "You are ranked #{}".format(ar+1)
            elif ar == -1: footer = "You aren't ranked ▫️ You need at least one roll to be ranked"
            else: footer = ""
            await ctx.send(embed=self.bot.buildEmbed(title="{} Spark ranking of {}".format(self.bot.getEmote('crown'), guild.name), color=self.color, description=msg, footer=footer, thumbnail=guild.icon_url))
        except Exception as e:
            await ctx.send(embed=self.bot.buildEmbed(title="Sorry, something went wrong :bow:", footer=str(e)))
            await self.bot.sendError("rollRanking", str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def quota(self, ctx):
        """Give you your GW quota for the day"""
        if ctx.author.id in self.bot.ids.get('branded', []):
            await ctx.send(embed=self.bot.buildEmbed(title="{} {} is a bad boy".format(self.bot.getEmote('gw'), ctx.author.display_name), description="Your account is **restricted.**", thumbnail=ctx.author.avatar_url, color=self.color))
            return

        h = random.randint(400, 2000)
        m = random.randint(70, 180)
        c = random.randint(1, 100)

        if ctx.author.id == self.bot.ids['wawi']:
            c = 7

        if c <= 2:
            c = random.randint(1, 110)
            if c == 1:
                await ctx.send(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got the **Eternal Battlefield Pass** 🤖\nCongratulations!!!\nYou will now revive GW over and ovḛ̸̛̠͕̑̋͌̄̎̍͆̆͑̿͌̇̇̕r̸̛̗̥͆͂̒̀̈́͑̑̊͐̉̎̚̚͝ ̵̨̛͔͎͍̞̰̠́͛̒̊̊̀̃͘ư̷͎̤̥̜̘͈̪̬̅̑͂̂̀̃̀̃̅̊̏̎̚͜͝ͅņ̴̢̛̛̥̮͖͉̻̩͍̱̓̽̂̂͌́̃t̵̞̦̿͐̌͗͑̀͛̇̚͝͝ỉ̵͉͕̙͔̯̯͓̘̬̫͚̬̮̪͋̉͆̎̈́́͛̕͘̚͠ͅļ̸̧̨̛͖̹͕̭̝͉̣̜͉̘͙̪͙͔͔̫̟̹̞̪̦̼̻̘͙̮͕̜̼͉̦̜̰̙̬͎͚̝̩̥̪̖͇̖̲̣͎̖̤̥͖͇̟͎̿̊͗̿̈̊͗̆̈́͋͊̔͂̏̍̔̒̐͋̄̐̄̅̇͐̊̈́̐͛͑̌͛̔͗̈́͌̀͑̌̅̉́̔̇́̆̉͆̄̂͂̃̿̏̈͛̇̒͆͗̈́̀̃̕̕͘̚̚͘͘͠͠͠͝͝͠͝͝ͅͅ ̴̢̛̛̛̯̫̯͕̙͙͇͕͕̪̩̗̤̗̺̩̬̞̞͉̱̊̽̇̉̏̃̑̋̋̌̎̾́̉́͌̿̐̆̒̾̆͒͛͌́͒̄͗͊͑̈́̑̐̂̿̋̊͊̈́̃̋̀̀̈̏̅̍̈͆̊̋͋̀̽͑̉̈́͘͘̕̕͝y̷̧̧̨̢̧̮̭̝̦͙͈͉̜͈̳̰̯͔͓̘͚̳̭͎̳̯͈͓̣͕͙̳̭̱͍͎͖̋͊̀͋͘͘ơ̸̢̗̖̹̹͖̣̫̝̞̦̘̙̭̮͕̘̱̆͋̓͗̾͐̉̏̀͂̄̎̂̈́͌͑̅̆̉̈̒͆̈̈̊͐̔̓̀̿̓̈́͝͝͝͠͝u̶̡̧̡̧̨̧̡̡̢̢̢̪̯͙͍̱̦̠̗̹̼̠̳̣͉̞̩̹͕̫͔͚̬̭̗̳̗̫̥̞̰̘̖̞̤͖̳̮̙͎͎̗̙̳͙͖͓̪̱̞͖̠̣̮̘͍̱̥̹͎͎̦̬̹̼̜͕͙͖̫̝̰̯̜̹̬̯͚͕̰̪̼͓̞̫̖̘͙̞͖̺̩͓̹̘̙̫̩̲̻̪̠̞̺͚̫̰̠̼̖̬͔̗̮͙̱̬̩̮̟͓̫̭̲̘̤͎̱̓̊̇́̀̏̏̾̀̄̆̒̂͐̌͂̈̂̓͋̌̓͘̕̕̚͜͜͜͝ͅͅͅͅŗ̷̡̧̨̢̢̢̧̡̡̧̡̢̧̨̨̡̧̛̛̛̬͚̮̜̟̣̤͕̼̫̪̗̙͚͉̦̭̣͓̩̫̞͚̤͇̗̲̪͕̝͍͍̫̞̬̣̯̤̮͉̹̫̬͕̫̥̱̹̲͔͔̪̖̱͔̹͈͔̳͖̩͕͚͓̤̤̪̤̩̰̬͙̞͙̘̯̮̫͕͚̙̜̼̩̰̻̞̺͈̝̝̖͎̻̹̞̥̰̮̥̙̠͔͎̤̲͎͍̟̥̞̗̰͓͍̞̹͍̬͎̲̬̞͈͉̼̥̝͈̼̠̫̙͖̪̼̲̯̲̫̼̺̘̗̘͚̤͓̯̦̣̬͒̑̒́͑͊̍̿̉̇̓̒̅̎͌̈́̐̽͋̏̒͂̈̒̃̿̓̇̈̿̊̎̈́͐̒͂͊̿̈́̿̅̏̀͐͛̎̍͑͂̈́̃̇̀̈͋̾̔̈́̽͌̿̍̇̅̏̋̑̈́̾̊͐̉̊̅͑̀͊̽̂̈́̽̓͗́̄͆̄͑͒̈́́͋̏͊͋̒͗̆̋̌̈̀͑͗̽͂̄̌̕͘͘̚͘̕̕͜͜͜͜͜͜͜͠͝͝͝͝͝͝ͅͅͅ ̷̧̡̧̨̢̧̨̡̨̧̛̛̛̛̮̭͇̣͓̙̺͍̟̜̞̫̪̘̼̞̜̠͇̗̮͕̬̥͓͔͈̟̦͇̥̖̭̝̱̗̠̘̝̹̖͓̝͇̖̫̯̩̞̞̯̲̤̱̻̤͇̲͍͈͓͖̹̗̟̲̪̪̟̩͙̪̝̮̘̽̋̍́̔̊̍̈́͂̌̽͒̆͐͊̏̐͑͛̓̆̈́͌̂͒͆̔̅̓̽͊̅́̾̽̓̏̆̀̀͌̾̀͒̓̇̊̀̐͛̌̋̈͑̇́̂̆̽̈̕̕̚̚͜͠ͅͅͅͅḑ̶̛̛̯͓̠̖͎̭̞̫͑̋̄̄̈̽̎̊͛̽͌̾̋̔̽̔̀̀͐̿̈́̀̃͐͂͆̈̃͑̀̋̑͊̃̆̓̾̎̅̀̆̓̏͊̆̔̈̅͛̍̎̓̀͛͒́̐͆̂̋̋͛̆̈͐͂̏̊̏̏̓̿̔͆̓̽̂̅͆̔͑̔̈̾̈̽̂̃̋̈́̾̎̈́̂̓̃̒͐͆̌̍̀͗̈́̑̌̚̕̕̚͠͠͝ę̴̧̨̨̨̢̨̢̧̧̧̨̧̛̛̛̛̛̛̛̺̪̹̘͈̣͔̜͓̥̥̟͇̱͚͖̠͙͙̱̞̣̤͚̣̟̫̬̟͓̺͙̬͚̹͓̗̬̼͇͙̻͍̖̙̥̩͔̜͕̖͕͔͚̳͙̩͇͙̺͔̲̱̙͉̝̠̤̝̭̮̩̦͇̖̳̞̞̖͎̙͙̲̮̠̣͍̪͙̰̣͉̘͉̦̖̳̫͖͖̘̖̮̲̱̪͕̳̫̫̞̪̜̞̬͙͖͍͖̦͉̯̟̖͇̩͚͙͔̳̫͗̈́̒̎͂̇̀͒̈́̃͐̉͛̾̑̆̃͐̈́̉͒̇̓̏̀͌̐͌̅̓͐́̿͒̅͑̍̓̈́̉̊́̉̀̔̊̍̽͛͛͆̓̈͋̉͋̿̉́̋̈̓̐̈́̔̃͆͗͛̏́̀̑͋̀̽̔̓̎̒̆̌̐̈́̓͂̐̋͊̌͑̓̈́̊̿͋̈́́̃̏̓̉͛͆̂͐͗͗̾̅̌̾͌̈́͊͘̕̚̕̚̚̕͘̕͜͜͜͜͜͜͜͠͝͝͠͝͝͠ͅͅa̸̡͔̯͎̟͙̖̗͔̺̰͇͚̭̲̭͕̫̜͉̯͕̅̈͋̒͋͂̐̕ͅţ̶̡̨̢̢̡̡̡̨̢̡̧̨̢̛̥̭̞͈̼̖͙͇̝̳͇̞̬͎̲̙̰̙̱̳̟̣̗̫̣͉͖̪̩͙̲͇͙̫̘͖̖̜̝̦̥̟̜̠͔̠͎̭͔̘͓͚̩͇͙͎͎̰̘̟̳̪͖̠̪̦̦̫̞̟̗̹̹̤͓͍̜̯͔̼̱̮̹͎͖͍̲͎̠͉̟͈̠̦̯̲̼̥̱̬̜͙̘͕̣̳͇̞͓̝͈̼̞̻͚̘̩̟̩̖̼͍̯̘͉͔̤̘̥̦͑̒͗̅̉̾͗̾̓̈́̍̉̈́͛̀͊̋̀͐̏̈́̀̀̍̇̀̀̈́̃̀̅͛̅̈́̇̽̆̌̈̄͆̄̂͂̔͗͌͊̽̿́͑̒̾̑̊̿͗́̇̋̊̄̀̍̓̆͂̆̔̏̍̑̔̊̾̎̆͛͑̓͒̈̎͌̓͗̀̿̓̃̔̈́͗̃̓̽̓̉̀͛͂̿́̀̌͊̆̋̀̓̇́̔̓͆̋̊̀̋͑́̔́̌̒̾̂̎̋̈́́̀͗̈́̈́́̾̈́͑͋̇͒̀͋͆͗̾͐̆̈́͂͐̈̐̓̍̈́̈̅̓͐̚̚̚̚̕͘̕͘̚̚̚͘͜͜͜͜͜͜͝͠͠͠͝͠ͅͅḥ̴̨̧̧̢̧̢̢̛̛̙̱͚̺̬̖̮̪͈̟͉̦̪̘̰̺̳̱̲͔̲̮̦̦̪̪̲̠͓͎͇͕̯̥͉͍̱̥͓̲̤̫̳̠̝͖̺̙͖͎͙̠͓̺̗̝̩͍͕͎̞͕̤̻̰̘͇͕̟̹̳͇͈͇̳̳̞̗̣͖̙͓̼̬̯͚͎̮͚̳̰͙̙̟̊͆͒͆͌̂̈́̀́̽̿͌̓́̐̑͌͋͆͊͑͛͑̀̋͐̏͌̑̀͛͗̀́̈̀̓̽̇̐̋͊̅͑̊͒̈́̀̀̔̀̇͗̆͑̅̌̑̈́͌̒̅̌̓͋͂̀̍̈́͐̈́̆̐̈́̍͛͂̔̐̎͂̎̇͑̈́̈́̎̉̈́́̒̒̆̌̃̓̈́͂̽̓̆̋̈̂̽̆̓̔͗̓̀̄̈́̂̏͗̐̔͘̕͘͘͜͜͜͜͠͠͝͠͠͝͝͝͠͠͝ͅͅ", thumbnail=ctx.author.avatar_url ,color=self.color))
            elif c <= 6:
                await ctx.send(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got a **Slave Pass** 🤖\nCongratulations!!!\nCall your boss and take a day off now!", footer="Full Auto and Botting are forbidden", thumbnail=ctx.author.avatar_url ,color=self.color))
            elif c <= 16:
                await ctx.send(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got a **Chen Pass** 😈\nCongratulations!!!\nYour daily honor or meat count must be composed only of the digit 6.", thumbnail=ctx.author.avatar_url ,color=self.color))
            elif c <= 21:
                await ctx.send(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got a **Carry Pass** 😈\nDon't stop grinding, continue until your Crew gets the max rewards!", thumbnail=ctx.author.avatar_url ,color=self.color))
            elif c <= 26:
                await ctx.send(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got a **Relief Ace Pass** 😈\nPrepare to relieve carries of their 'stress' after the day!!!", footer="wuv wuv", thumbnail=ctx.author.avatar_url ,color=self.color))
            else:
                await ctx.send(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="You got a **Free Leech Pass** 👍\nCongratulations!!!", thumbnail=ctx.author.avatar_url ,color=self.color))
            return
        elif c == 3:
            h = h * random.randint(50, 80)
            m = m * random.randint(50, 80)
        elif c <= 6:
            h = h * random.randint(20, 30)
            m = m * random.randint(20, 30)
        elif c <= 9:
            h = h * random.randint(8, 15)
            m = m * random.randint(8, 15)
        elif c == 10:
            h = h // random.randint(30, 50)
            m = m // random.randint(30, 50)
        elif c <= 12:
            h = h // random.randint(10, 20)
            m = m // random.randint(10, 20)
        elif c <= 14:
            h = h // random.randint(3, 6)
            m = m // random.randint(3, 6)
        h = h * 100000
        m = m * 10

        if ctx.author.id == self.bot.ids['chen']:
            c = random.randint(3, 8)
            if c == 3: h = 666
            elif c == 4: h = 6666
            elif c == 5: h = 66666
            elif c == 6: h = 666666
            elif c == 7: h = 6666666
            elif c == 8: h = 66666666
            c = random.randint(1, 4)
            if c == 1: m = 6
            elif c == 2: m = 66
            elif c == 3: m = 666
            elif c == 4: m = 6666

        await ctx.send(embed=self.bot.buildEmbed(title="{} {}'s daily quota".format(self.bot.getEmote('gw'), ctx.author.display_name), description="**Honor:** {:,}\n**Meat:** {:,}".format(h, m), thumbnail=ctx.author.avatar_url ,color=self.color))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isGBFGgeneralAndMod()
    @commands.cooldown(1, 180, commands.BucketType.user)
    async def pitroulette(self, ctx, max : int = 1):
        """Game for /gbfg/ (Mod only)"""
        if not self.pitroulettestate:
            if max < 1 or max > 5:
                await ctx.send(embed=self.bot.buildEmbed(title="Value must be in the 1-5 range" ,color=self.color))
                return
            self.pitroulettestate = True
            self.pitroulettecount = 0
            self.pitroulettemax = max
            self.pitroulettevictim = []
            self.pitroulettelist = []
            await ctx.send(embed=self.bot.buildEmbed(title="Pit Roulette enabled", description=random.choice(["Who will fall in?", "Are you brave enough?", "Do you dare?"]) , thumbnail="https://cdn.discordapp.com/attachments/354370895575515138/584813271643586560/Activate_it.png", footer="expecting " + str(max) + " victim(s)", color=self.color))
        else:
            await ctx.send(embed=self.bot.buildEmbed(title="Pit Roulette already on" ,color=self.color))

    async def pitroulette_callback(self, message):
        try:
            if self.pitroulettestate and self.pitroulettemax > 0 and message.channel.id == self.bot.ids['gbfg_general'] and message.author.id != self.bot.ids['owner'] and not message.author.bot:
                self.pitroulettecount += 1
                proba = 3 * (self.pitroulettemax + 1)
                if random.randint(1, 100) <= proba:
                    self.pitroulettevictim.append(message)
                    self.bot.runTask('pitroulette', self.pitroulettetask)
                    self.pitroulettemax -= 1
                    return False
        except Exception as e:
            await self.bot.sendError('pitroulette callback', str(e))
        return True

    # TO REWRITE
    async def pitroulettetask(self):
        try:
            message = self.pitroulettevictim.pop()
            self.pitroulettelist.append([message.author.display_name, self.pitroulettecount, message.content, "[**Link**](https://discordapp.com/channels/{}/{}/{})".format(message.guild.id, message.channel.id, message.id)])
            description = "After **{}** message(s)".format(self.pitroulettecount)
            title = random.choice(["{} has fallen into the pit...", "{} tripped and fell...", "{} jumped into the pit willingly...", "{} got pushed in the back..."]).format(message.author.display_name)
            footer = random.choice(["Will {} manage to climb up?".format(message.author.display_name), "Stay down here where you belong", "Straight into the hellish pit", "{} has met with a terrible fate".format(message.author.display_name)])
            if self.pitroulettemax > 0:
                description += "\nI'm expecting **{}** more victim(s)".format(self.pitroulettemax)
            else:
                self.pitroulettestate = False # disable
            await message.channel.send(embed=self.bot.buildEmbed(title=title, description=description, thumbnail=message.author.avatar_url, footer=footer))
            if self.pitroulettemax == 0 and len(self.pitroulettelist) > 1:
                fields = []
                for a in self.pitroulettelist:
                    if len(a[2]) == 0: fields.append({'name': "{} ▫️ after {} message(s)".format(a[0], a[1]), 'value':a[3]})
                    else: fields.append({'name': "{} ▫️ after {} message(s)".format(a[0], a[1]), 'value':'{}\n{}'.format(a[2], a[3])})
                await message.channel.send(embed=self.bot.buildEmbed(title="Pit Roulette results", fields=fields, inline=False, thumbnail=message.author.avatar_url))
            g = self.bot.get_guild(self.bot.ids['gbfg'])
            await message.author.add_roles(g.get_role(self.bot.ids['pit']))
            await asyncio.sleep(60)
            await message.author.remove_roles(g.get_role(self.bot.ids['pit']))
        except asyncio.CancelledError:
            try:
                await message.author.remove_roles(g.get_role(self.bot.ids['pit']))
            except:
                pass
            return
        except Exception as e:
            await self.bot.sendError('pitroulette', str(e))

    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @isAuthorized()
    @commands.cooldown(2, 7, commands.BucketType.user)
    async def character(self, ctx):
        """Generate a random GBF character"""
        seed = (ctx.author.id + int(datetime.utcnow().timestamp()) // 86400) % 4428
        rarity = ['SSR', 'SR', 'R']
        race = ['Human', 'Erun', 'Draph', 'Harvin', 'Primal', 'Other']
        element = ['fire', 'water', 'earth', 'wind', 'light', 'dark']

        await ctx.send(embed=self.bot.buildEmbed(author={'name':"{}'s daily character".format(ctx.author.display_name), 'icon_url':ctx.author.avatar_url}, description="**Rarity** ▫️ {}\n**Race** ▫️ {}\n**Element** ▫️ {}\n**Rating** ▫️ {:.1f}".format(self.bot.getEmote(rarity[seed % 3]), race[(seed - 1) % 6], self.bot.getEmote(element[(seed - 3) % 6]), ((seed % 41) * 0.1) + 6.0 - (seed % 3) * 1.5), inline=True, color=self.color))


    @commands.command(no_pm=True, cooldown_after_parsing=True)
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def xil(self, ctx):
        """Generate a random element for Xil"""
        g = random.Random()
        elems = ['fire', 'water', 'earth', 'wind', 'light', 'dark']
        g.seed(int((int(datetime.utcnow().timestamp()) // 86400) * (1.0 + 1.0/4.2)))
        e = g.choice(elems)

        await ctx.send(embed=self.bot.buildEmbed(title="Today, Xil's main element is", description="{} **{}**".format(self.bot.getEmote(e), e.capitalize()), color=self.color))