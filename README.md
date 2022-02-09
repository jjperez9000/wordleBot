WordleBot™ is a bot designed to track people's score in Wordle. 
To get your own instance of WordleBot™ running, just copy this code in and also make a secrets 
folder in the repository. That folder should contain 3 files: cfg.json, token.json, and scores.json

wordleBot/secrets/cfg.json
wordleBot/secrets/token.json
wordleBot/secrets/scores.json

cfg.json should have a server ID labeled "guild" and a channel ID named "channel"
These IDs represent the server that the bot will live in and the channel that it will pay attention to. 

{
    "guild":12345
    "channel":12345
}

token.json should have a token that represents the bot's token.

{
    "token":qwiofhjqe3opij34fLJFklseJFLJjiqweojf3q8p43ofj3
}

finally scores.json just needs to be a valid json file. 

{

}
