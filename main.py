# bot.py
import json
import discord
from discord.utils import get
from datetime import datetime
import threading
import pytz

intents = discord.Intents().all()
client = discord.Client(prefix='', intents=intents)

with open('secrets/cfg.json', 'r') as f:
    data = json.load(f)
    currentGuild = data["guild"]
    responseChannel = data["channel"]

@client.event
async def on_message(message):
    print(message.author.id)
    if message.author == client.user or message.channel.id != responseChannel:
        return

    # this will break after day 999
    # handle wordle submissions
    channel = client.get_channel(responseChannel)
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
    elif message.content == '!reset' and message.author.id == 261236642680012802:
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

    await channel.send("Stats for **" + str(user) + "**. Completed " + str(completions) + ". Total Score: " + str(score))


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
            players.append({'id':player, key:data[player][key]})

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
            # name = await client.fetch_user(int(player_id))
            name_formatter = '{message:{fill}{align}{width}}'.format(
               # message=name.nick,
               message=name.display_name,
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
            leaderboard += str(i) + ". " + name_formatter + " | " + score_formatter + " | " + str(data[str(name.id)]["completions"]) + "\n"
            i += 1
        leaderboard += "```"
        await channel.send(leaderboard)


def create_user(id):
    new_user = {str(id):
                    {
                        "total_score": 0,
                        "playedToday": False,
                        "completions": 0,
                        "weekly_score": 0,
                        "recent_scores": [0, 0, 0, 0, 0, 0, 0]
                    }
                }
    return new_user


async def inject_score(user_list, user, score):
    score = 7 - score
    user_list[user]["total_score"] += score
    user_list[user]["weekly_score"] = user_list[user]["weekly_score"] + score - user_list[user]["recent_scores"][6]

    for i in range(6, 0, -1):
        user_list[user]["recent_scores"][i] = user_list[user]["recent_scores"][i - 1]
    user_list[user]["recent_scores"][0] = score

    top_score = 0
    top_wordler = ""

    for player in user_list:
        if user_list[player]["weekly_score"] > top_score:
            top_score = user_list[player]["weekly_score"]
            top_wordler = player

    guild = client.get_guild(currentGuild)
    role = get(guild.roles, name='Top Wordler')
    winner = guild.get_member(int(top_wordler))
    if winner != role.members[0]:
        await role.members[0].remove_roles(role)
    await winner.add_roles(role)

    return user_list


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
            # data[str(message.author.id)]["total_score"] += 7 - int(message.content[12])
            # data[str(message.author.id)]["completions"] += 1
            data = await inject_score(data, str(message.author.id), int(message.content[12]))
            if int(message.content[12]) == 1:
                guess = " guess"
            else:
                guess = " guesses"
            await channel.send("Today's score received: " + str(7 - int(message.content[12])) + " points for " +
                               str(message.content[12]) + guess + ". " +
                               str(client.get_guild(currentGuild).get_member(int(message.author.id)).display_name) +
                               "'s total: " + str(data[str(message.author.id)]["total_score"]))

        data[str(message.author.id)]["playedToday"] = True

    with open('secrets/scores.json', 'w') as f:
        f.write(json.dumps(data, indent=4))


def daily_reset():
    threading.Timer(1, daily_reset).start()
    tz = pytz.timezone('US/Eastern')
    now = datetime.now(tz)
    current_time = now.strftime("%H:%M:%S")
    # print("Current Time =", current_time)
    if current_time == '00:00:00':
        # print("test")
        print("working")
        with open('secrets/scores.json', 'r') as f:
            data = json.load(f)
            for player in data:
                data[player]['playedToday'] = False
        with open('secrets/scores.json', 'w') as f:
            f.write(json.dumps(data, indent=4))


daily_reset()

# wordlebot toeken
with open('secrets/token.json', 'r') as f:
    token = str(json.load(f)['token'])
    client.run(token)

