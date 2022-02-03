# bot.py
import json
import discord
from datetime import datetime
import threading

intents = discord.Intents().all()
client = discord.Client(prefix='', intents=intents)

with open('cfg.json', 'r') as f:
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
    if message.content[:7] == '!Wordle':
        await handle_submission(message)
    elif message.content == '!leaderboard':
        await print_leaderboard(message)
    elif message.content == '!help':
        await print_help(message)
    elif message.content[:6] == '!stats':
        await print_stats(message)
    elif message.content == '!test':
        print("working")

        channel = client.get_channel(responseChannel)
        await channel.send("test!")


async def print_stats(message):

    channel = client.get_channel(responseChannel)
    user = str(client.get_guild(currentGuild).get_member(int(message.author.id)).display_name)
    with open('scores.json', 'r') as f:
        data = json.load(f)
        score = data[str(message.author.id)]["score"]
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

def sortFunction(e):
    return e['score']


async def print_leaderboard(message):
    with open('scores.json', 'r') as f:

        data = json.load(f)
        channel = client.get_channel(responseChannel)

        players = []
        for player in data:
            players.append({'id':player, 'score':data[player]['score']})
        players.sort(key=sortFunction, reverse=True)

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
                message=str(player['score']),
                fill=' ',
                align='<',
                width=5,
            )
            leaderboard += str(i) + ". " + name_formatter + " | " + score_formatter + " | " + str(data[str(name.id)]["completions"]) + "\n"
            i += 1
        leaderboard += "```"
        await channel.send(leaderboard)


async def handle_submission(message):
    # open score file
    with open('scores.json', 'r') as f:

        data = json.load(f)
        channel = client.get_channel(responseChannel)

        # check if user is new or not
        if str(message.author.id) not in data:
            print("added new user")
            new_user = {str(message.author.id): {"score": 0, "playedToday": False, "completions": 0}}
            data.update(new_user)

        # make sure user hasn't submitted already if they exist
        if data[str(message.author.id)]["playedToday"]:
            await channel.send("Only one score submission allowed per day.")
        # check if user failed
        elif message.content[12] == 'X':
            data[str(message.author.id)]["playedToday"] = True
            await channel.send("lol dumbass")
        # if no fail then update score
        else:
            print("user already in")
            data[str(message.author.id)]["score"] += 7 - int(message.content[12])
            data[str(message.author.id)]["playedToday"] = True
            data[str(message.author.id)]["completions"] += 1
            if int(message.content[12]) == 1:
                guess = " guess"
            else:
                guess = " guesses"
            await channel.send("Today's score received: " + str(7 - int(message.content[12])) + " points for " + str(message.content[12]) + guess +
                               ". " + str(client.get_guild(currentGuild).get_member(int(message.author.id)).display_name) + "'s total: " + str(data[str(message.author.id)]["score"]))

    with open('scores.json', 'w') as f:
        f.write(json.dumps(data, indent=4))


def daily_reset():
    threading.Timer(1, daily_reset).start()
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    # print("Current Time =", current_time)
    # if current_time == '00:00:00':
    if current_time == '00:00:00':
        with open('scores.json', 'r') as f:
            data = json.load(f)
            for player in data:
                data[player]['playedToday'] = False
        with open('scores.json', 'w') as f:
            f.write(json.dumps(data, indent=4))


daily_reset()

# wordlebot toeken
client.run('OTM1NTQ3NzEwMjQ3OTI3ODU5.YfAOsw.lbNzjzb_Gczps13sq8SFAQ907zY')
# ttetsBot toeken
# client.run('OTM1OTk2NTc1MDMxODk0MDQ2.YfGwvQ.bhSupVFpSe_kFKRDFI83bE_H_Zg')


