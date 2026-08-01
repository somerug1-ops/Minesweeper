import os
import sys
import logging
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from game import Minefield
from views import UiBoard, ActionControl
from stats import StatsManager

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("minesweeper")

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
stats = StatsManager()

@bot.event
async def on_ready():
    logger.info("Logged in as %s (ID: %d)", bot.user, bot.user.id)
    try:
        synced = await bot.tree.sync()
        logger.info("Synced %d command(s) globally", len(synced))
        for guild in bot.guilds:
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
    except Exception as err:
        logger.error("Failed to sync commands: %s", err)

@bot.tree.command(name="minesweeper", description="Start an interactive 5x5 Minesweeper game")
async def minesweeper(interaction: discord.Interaction):
    await interaction.response.defer()

    board = Minefield(rows=5, cols=5, mines=5)
    board_view = UiBoard(board=board, user_id=interaction.user.id, username=interaction.user.display_name, stats_mgr=stats)
    board_view.sync_ui()
    
    embed = board_view.make_embed()
    msg = await interaction.followup.send(embed=embed, view=board_view)
    board_view.msg_ref = msg

    action_view = ActionControl(ui=board_view)
    board_view.action_view = action_view
    await interaction.followup.send(view=action_view)

@bot.tree.command(name="play", description="Alias for starting a 5x5 game")
async def play(interaction: discord.Interaction):
    await minesweeper(interaction)

@bot.tree.command(name="spoilers", description="Generate a text-based spoiler board")
@app_commands.choices(
    size=[
        app_commands.Choice(name="Small (6x6)", value="small"),
        app_commands.Choice(name="Medium (8x8)", value="medium"),
        app_commands.Choice(name="Large (10x10)", value="large"),
        app_commands.Choice(name="Huge (12x12)", value="huge"),
        app_commands.Choice(name="Insane (14x14)", value="insane"),
        app_commands.Choice(name="Nightmare (15x15)", value="nightmare"),
    ]
)
async def spoilers(interaction: discord.Interaction, size: str = "medium"):
    await interaction.response.defer()

    grid_sizes = {
        "small": (6, 6, 6),
        "medium": (8, 8, 10),
        "large": (10, 10, 16),
        "huge": (12, 12, 25),
        "insane": (14, 14, 35),
        "nightmare": (15, 15, 45),
    }

    rows, cols, mines = grid_sizes.get(size, (8, 8, 10))
    board = Minefield(rows=rows, cols=cols, mines=mines)
    spoiler_text = board.to_spoilers()

    embed = discord.Embed(
        title=f"Minesweeper ({rows}x{cols})",
        description=f"**Mines:** `{mines}`\nUncover spoiler tags to reveal tiles!\n\n{spoiler_text}",
        color=discord.Color.purple()
    )
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="stats", description="Check player statistics")
async def show_stats(interaction: discord.Interaction, user: discord.User = None):
    await interaction.response.defer()

    target = user or interaction.user
    user_stats = stats.get_user_stats(target.id)

    played = user_stats.get("games_played", 0)
    wins = user_stats.get("wins", 0)
    losses = user_stats.get("losses", 0)
    win_rate = (wins / played * 100) if played > 0 else 0.0
    cleared = user_stats.get("mines_cleared", 0)

    embed = discord.Embed(
        title=f"Stats: {target.display_name}",
        color=discord.Color.teal()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="Games Played", value=f"`{played}`", inline=True)
    embed.add_field(name="Wins", value=f"`{wins}`", inline=True)
    embed.add_field(name="Losses", value=f"`{losses}`", inline=True)
    embed.add_field(name="Win Rate", value=f"`{win_rate:.1f}%`", inline=True)
    embed.add_field(name="Mines Cleared", value=f"`{cleared}`", inline=True)

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="leaderboard", description="View server Minesweeper leaderboard")
@app_commands.choices(
    category=[
        app_commands.Choice(name="Most Wins", value="wins"),
        app_commands.Choice(name="Highest Win Rate", value="win_rate"),
    ]
)
async def leaderboard(interaction: discord.Interaction, category: str = "wins"):
    await interaction.response.defer()

    top_players = stats.get_leaderboard(category=category, limit=10)
    if not top_players:
        await interaction.followup.send("No game stats recorded yet.", ephemeral=True)
        return

    embed = discord.Embed(title="Minesweeper Leaderboard", color=discord.Color.gold())
    lines = []
    for idx, entry in enumerate(top_players):
        uid = entry["user_id"]
        if category == "win_rate":
            val = f"{entry['win_rate']}% WR ({entry['wins']} wins)"
        else:
            val = f"{entry['wins']} wins ({entry['win_rate']}% WR)"
        lines.append(f"`#{idx+1}` <@{uid}> — **{val}**")

    embed.description = "\n".join(lines)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="help", description="How to play and list of commands")
async def help_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    embed = discord.Embed(
        title="Minesweeper Guide",
        description="Here is how to play and available commands:",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="Commands",
        value=(
            "• `/play` or `/minesweeper` - Play 5x5 button game\n"
            "• `/spoilers [size]` - Generate text spoiler board\n"
            "• `/stats [user]` - View user statistics\n"
            "• `/leaderboard` - Server leaderboard\n"
            "• `/help` - Show this menu"
        ),
        inline=False
    )
    embed.add_field(
        name="Game Rules",
        value=(
            "1. Use the **Mode** toggle button to switch between Reveal and Flag.\n"
            "2. Click cells on the grid to act.\n"
            "3. Numbers indicate how many mines are touching that square.\n"
            "4. Uncover all non-mine tiles to win!"
        ),
        inline=False
    )
    await interaction.followup.send(embed=embed, ephemeral=True)

if __name__ == "__main__":
    if not TOKEN:
        logger.error("No DISCORD_TOKEN set in environment or .env file.")
        sys.exit(1)

    bot.run(TOKEN)

