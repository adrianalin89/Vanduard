**Vanduard is a discord bot** created to change the way servers work, instead of having permanent channels you can now create temporary ones that delete themselves once they are empty. This is a POC and i mainly made it for my "clan" for the game Destiny2. 

_The bot is programmed via [**discord.py**](https://pypi.org/project/discord.py/) and it's tested with Python 3.9_
# Requirements
- [discord.py](https://pypi.org/project/discord.py/)
- [validators](https://pypi.org/project/validators/)
# Setup the bot:

1. Download python using the following link:

- [https://www.python.org/downloads/](https://www.python.org/downloads/)

2. Clone the bot from GitHub

3. Open the terminal and follow these steps:

- Change directory to this folder and type:

- `pip install -r requirements.txt`

4. Open `bot.py` in a text editor and replace `"Insert Discord token here"` with your token bot

5. Open `cogs/voice.py` in a text editor and replace `"OWNER_ID"` with your owner id, `"USER_ROLE_ID"` with user role id and `"STAFF_ROLE_ID"` with staff id which can bypass the maximum number of channels

6. Run the bot

**Remember to enable the "PRESENCE INTENT" and "SERVER MEMBERS INTENT" on [Discord Devolper Portal](https://discord.com/developers/applications/)**
# Usage
For setup bot use `.voice setup` command

For the command list use `.help` command