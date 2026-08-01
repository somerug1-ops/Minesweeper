# discord-minesweeper

A simple Minesweeper Discord bot built with `discord.py`. Plays directly in chat using interactive button grids or spoiler text tags.

## Features
- **Interactive Grid**: Play 5x5 Minesweeper using Discord button components.
- **Reveal & Flag Modes**: Switch between revealing tiles and flagging suspected mines.
- **Spoiler Boards**: Generate spoiler-tagged text boards (`/spoilers`) for instant chat games without interactive buttons.
- **Leaderboards & Stats**: Tracks wins, win rates, and total mines cleared saved locally in JSON.

## Quickstart

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your bot token**
   Create a `.env` file in the project folder:
   ```env
   DISCORD_TOKEN=your_bot_token_here
   ```

3. **Run the bot**
   ```bash
   python bot.py
   ```

## Bot Commands

| Command | Description |
| --- | --- |
| `/play` or `/minesweeper` | Starts an interactive 5x5 button game |
| `/spoilers [size]` | Spawns a spoiler text board (Small to Nightmare) |
| `/stats [user]` | Displays stats (games played, win rate, mines cleared) |
| `/leaderboard [category]` | Top 10 players ranked by wins or win rate |
| `/help` | Shows game instructions and command info |

## Bot Permissions Needed
Make sure to invite the bot with the `applications.commands` and `bot` scopes (Send Messages, Embed Links).

