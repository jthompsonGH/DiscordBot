* Discord Bot

- Basic bot made with [discord.py](https://discordpy.readthedocs.io/en/stable/) that manages a simple local JSON "database" that keeps track of shows, their status (planned/watching/watched), and their comments. 
- Also lets users play Tic Tac Toe and Rock Paper Scissors against one another, flip a coin to see the result, and has a random chance of "shmoogling" them (literally just replied with the word "shmoogle").
- Can also be used for generating Discord timestamps, and has some functionality to allow the host (`os.environ.get("DEV_USER_ID")`) to write out some development logs for their projects if they'd like.
