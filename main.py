# bot.py
import json
import random
import emoji
import discord
from discord.utils import get
from datetime import datetime
import threading
import pytz
from collections import OrderedDict
import calendar
from datetime import date

intents = discord.Intents().all()
client = discord.Client(prefix='', intents=intents)
john = 261236642680012802

with open('secrets/cfg.json', 'r') as f:
    data = json.load(f)
    currentGuild = data["guild"]
    responseChannel = data["channel"]

destinationChannel = None
@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))
    global destinationChannel
    destinationChannel = client.get_channel(responseChannel)


@client.event
async def on_message(message):
    global destinationChannel

    print(message.author.id)
    channel = client.get_channel(responseChannel)

    # code for wordlebot to talk
    if type(message.channel) == discord.channel.DMChannel:
        print("DM : " + message.author.name + " : " + message.content)
    else:
        print(message.channel.name + " : " + message.author.name + " : " + message.content)
    # if john sends a message, repeat it in channel
    if message.author != client.user and type(message.channel) == discord.channel.DMChannel and message.author.id == john:
        if ('!changechan' in message.content):
            command = message.content.split(' ')
            destinationChannel = client.get_channel(int(command[1]))
        else:
            await destinationChannel.send(message.content)

    # make sure message is valid
    if message.author == client.user or message.channel.id != responseChannel:
        return

    # this will break after day 999
    # handle wordle submissions
    if message.content[:7] == '!Wordle':
        await handle_submission(message)
    elif message.content[:12] == '!leaderboard':
        if message.content[13:] == 'weekly':
            await print_leaderboard(message, "weekly_score")
        else:
            await print_leaderboard(message, "total_score")
    elif message.content == '!help':
        await print_help(message)
    elif message.content[:6] == '!stats':
        await print_stats(message)
    elif message.content == '!test':
        print("working")
        await channel.send("test!")
    elif message.content == '!reset' and message.author.id == john:
        await channel.send("resetting the day, captain")
        await force_reset()
    elif message.content == '!reset':
        await channel.send("fuck off")
    elif message.content == 'o7':
        await channel.send('o7')


async def force_reset():
    with open('secrets/scores.json', 'r') as f:
        data = json.load(f)
        for player in data:
            data[player]['playedToday'] = False
    with open('secrets/scores.json', 'w') as f:
        f.write(json.dumps(data, indent=4))


async def print_stats(message):
    channel = client.get_channel(responseChannel)
    user = str(client.get_guild(currentGuild).get_member(int(message.author.id)).display_name)
    with open('secrets/scores.json', 'r') as f:
        data = json.load(f)
        score = data[str(message.author.id)]["total_score"]
        completions = data[str(message.author.id)]["completions"]
    averageScore = score/completions
    await channel.send("Stats for **" + str(user) + "**. Completed " + str(completions) + ". Total Score: " + str(score) + " Average Score: " + str(averageScore)[:4])


async def print_help(message):
    channel = client.get_channel(responseChannel)
    await channel.send("**WordleBot™** tracks wordle scores over time. \n\n"
                       "Users may submit once a day by typing an ! followed by a paste of the text that gets copied \n"
                       "when clicking 'share' following a win or loss. Points are calculated based on how many \n"
                       "attempts it took to solve the wordle that day.\n\n"
                       "example:\n"
                       "!Wordle 220 1/6 \n🟩🟩🟩🟩🟩\n\n"
                       "**This bot, just like the game, is completely honor based. If you cheat you should be ashamed of yourself for taking a silly word game so seriously**\n"
                       "*don't make me beg*\n\n"
                       "Score is calculated as 7 - num_attempts, \ne.g. getting the word 1st try is "
                       "worth 6 points and getting the word in 6 tries is worth 1 point\n\n"
                       "(Sydney's points are halved for balancing purposes)\n\n"
                       "**Other commands:** \n"
                       "!leaderboard -> shows the current standings\n"
                       "!stats -> shows your current stats")


def sortTotal(data):
    return data["total_score"]


def sortWeekly(data):
    return data["weekly_score"]


async def print_leaderboard(message, key):
    with open('secrets/scores.json', 'r') as f:

        data = json.load(f)
        channel = client.get_channel(responseChannel)

        players = []
        for player in data:
            players.append({'id': player, key: data[player][key]})

        if key == "weekly_score":
            players.sort(key=sortWeekly, reverse=True)
        else:
            players.sort(key=sortTotal, reverse=True)

        i = 1
        leaderboard = "```"
        leaderboard += '{message:{fill}{align}{width}}'.format(
            message="   standings:",
            fill=' ',
            align='<',
            width=15,
        ) + " | score | completions\n"

        guild = client.get_guild(currentGuild)
        for player in players:
            player_id = player['id']
            name = guild.get_member(int(player_id))
            if name is None:
                continue

            real_name = emoji.demojize(name.display_name)
            if (len(real_name) > 12):
                list1 = list(real_name)
                list1[9] = '.'
                list1[10] = '.'
                list1[11] = '.'
                real_name = ''.join(list1)

            # name = await client.fetch_user(int(player_id))
            name_formatter = '{message:{fill}{align}{width}}'.format(
                # message=name.nick,
                message=real_name[:12],
                fill=' ',
                align='<',
                width=12,
            )
            score_formatter = '{message:{fill}{align}{width}}'.format(
                message=str(player[key]),
                fill=' ',
                align='<',
                width=5,
            )
            leaderboard += str(i) + ". " + name_formatter + " | " + score_formatter + " | " + str(
                data[str(name.id)]["completions"]) + "\n"
            i += 1
        leaderboard += "```"
        await channel.send(leaderboard)


def create_user(id):
    new_user = {str(id):
        {
            "total_score": 0,
            "playedToday": False,
            "completions": 0,
            "weekly_score": 0
        }
    }
    return new_user


async def inject_score(data, user, score):
    # increment user score
    score = 7 - score
    data[user]["total_score"] += score
    data[user]["weekly_score"] += score

    guild = client.get_guild(currentGuild)
    role = get(guild.roles, name='Top Wordler')

    best_score = 0
    top_wordler = None

    for player in data:
        if data[player]['weekly_score'] > best_score:
            top_wordler = player
            best_score = data[player]['weekly_score']

    for player in role.members:
        await player.remove_roles(role)
    await guild.get_member(int(top_wordler)).add_roles(role)

    return data


async def handle_submission(message):
    # open score file
    with open('secrets/scores.json', 'r') as f:

        data = json.load(f)
        channel = client.get_channel(responseChannel)

        # check if user is new or not
        if str(message.author.id) not in data:
            print("added new user")
            new_user = create_user(message.author.id)
            data.update(new_user)

        # make sure user hasn't submitted already if they exist
        if data[str(message.author.id)]["playedToday"]:
            await channel.send("Only one score submission allowed per day.")
        # check if user failed
        elif message.content[12] == 'X':
            await channel.send("lol dumbass")
            data = await inject_score(data, str(message.author.id), 7)
        else:
            data[str(message.author.id)]["completions"] += 1
            data = await inject_score(data, str(message.author.id), int(message.content[12]))
            if int(message.content[12]) == 1:
                guess = " guess"
            else:
                guess = " guesses"
            await channel.send("Today's score received: " + str(7 - int(message.content[12])) + " points for " +
                               str(message.content[12]) + guess + ". " +
                               str(client.get_guild(currentGuild).get_member(int(message.author.id)).display_name) +
                               "'s total: " + str(data[str(message.author.id)]["total_score"]))
            await send_snark(int(message.content[12]), channel)

        data[str(message.author.id)]["playedToday"] = True

    with open('secrets/scores.json', 'w') as f:
        f.write(json.dumps(data, indent=4))


async def send_snark(guesses, channel):
    # messages = [
    #     ["fuck you"],
    #     ["kinda sus"],
    #     ["thank you Sydney, very cool", "impressive!", "you must feel pretty good right about now",
    #      "stop you're making everyone jealous", "poggers",
    #      "this has been the highlight of my day. I have a boring life"],
    #     ["birdie", "wow you did slightly better than average", "nice job", "three is like one less than four, crazy"],
    #     ["Wow that's so average", "holy shit you did fine", "kinda expected, coming from you", "meh.",
    #      "my job is so dull sometimes"],
    #     ["rough day", "oooh that's tough", "at least it's not 6 :)", "wooooooooah, you suck", "you can do better",
    #                                                                     "I guess somebody had to suck today"],
    #     ["by the skin of your teeth!", "at least you didn't lose :)", "le mao",
    #      "wow that's the worst I've seen all day",
    #      "you must be joking", "L + ratio", ":copium::copium::copium:"]
    # ]
    with open('secrets/quips.json', 'r') as f:
        data = json.load(f)
        messages = data

    await channel.send(messages[str(guesses)][random.randint(0, len(messages[str(guesses)]) - 1)])


def daily_reset():
    threading.Timer(1, daily_reset).start()
    tz = pytz.timezone('US/Eastern')
    now = datetime.now(tz)
    current_time = now.strftime("%H:%M:%S")
    if current_time == '00:00:00':
        # print("test")
        print("working")
        channel = client.get_channel(responseChannel)
        # await channel.send("resetting the day")
        with open('secrets/scores.json', 'r') as f:
            data = json.load(f)
            for player in data:
                data[player]['playedToday'] = False

            weekly_reset(data)

        with open('secrets/scores.json', 'w') as f:
            f.write(json.dumps(data, indent=4))


def weekly_reset(data=None):
    if data is None:
        return
    if datetime.today().isoweekday() == 7:
        for player in data:
            data[player]['weekly_score'] = 0


daily_reset()
weekly_reset()

# wordlebot toeken
with open('secrets/token.json', 'r') as f:
    token = str(json.load(f)['token'])
    client.run(token)
