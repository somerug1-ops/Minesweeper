import logging
import discord
from discord import ButtonStyle, Interaction
from discord.ui import View, Button
from game import Minefield
from stats import StatsManager

logger = logging.getLogger("minesweeper")

class GridButton(Button):
    def __init__(self, row: int, col: int):
        super().__init__(style=ButtonStyle.secondary, label="❓", row=row)
        self.r = row
        self.c = col

    async def callback(self, interaction: Interaction):
        ui: UiBoard = self.view
        if interaction.user.id != ui.user_id:
            await interaction.response.send_message("This isn't your game! Use `/play` to start your own.", ephemeral=True)
            return

        if ui.board.game_over:
            await interaction.response.send_message("This game is already over! Use `/play` to start a new game.", ephemeral=True)
            return

        if ui.mode == "reveal":
            ui.board.step(self.r, self.c)
        else:
            ui.board.flag(self.r, self.c)

        if ui.board.game_over and not ui.stats_saved:
            ui.stats_saved = True
            ui.stats_mgr.record_game(
                user_id=ui.user_id,
                won=ui.board.won,
                elapsed_seconds=ui.board.time_taken(),
                mines_count=ui.board.mines
            )

        ui.sync_ui()
        embed = ui.make_embed()

        if ui.action_view:
            ui.action_view.sync_state()

        await interaction.response.edit_message(embed=embed, view=ui)


class ToggleModeButton(Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.success, label="Mode: Reveal", custom_id="mode_toggle")

    async def callback(self, interaction: Interaction):
        ctrl: ActionControl = self.view
        ui: UiBoard = ctrl.ui

        if interaction.user.id != ui.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return

        if ui.mode == "reveal":
            ui.mode = "flag"
            self.style = ButtonStyle.primary
            self.label = "Mode: Flag"
        else:
            ui.mode = "reveal"
            self.style = ButtonStyle.success
            self.label = "Mode: Reveal"

        embed = ui.make_embed()
        await interaction.response.edit_message(view=ctrl)
        if ui.msg_ref:
            try:
                await ui.msg_ref.edit(embed=embed, view=ui)
            except discord.HTTPException as err:
                logger.error("Error updating board message: %s", err)


class QuitButton(Button):
    def __init__(self):
        super().__init__(style=ButtonStyle.danger, label="Give Up", custom_id="quit_game")

    async def callback(self, interaction: Interaction):
        ctrl: ActionControl = self.view
        ui: UiBoard = ctrl.ui

        if interaction.user.id != ui.user_id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return

        if ui.board.game_over:
            await interaction.response.send_message("Game is already over!", ephemeral=True)
            return

        ui.board.game_over = True
        ui.board.won = False
        
        for row in ui.board.grid:
            for cell in row:
                if cell.is_mine:
                    cell.is_revealed = True

        if not ui.stats_saved:
            ui.stats_saved = True
            ui.stats_mgr.record_game(
                user_id=ui.user_id,
                won=False,
                elapsed_seconds=ui.board.time_taken(),
                mines_count=ui.board.mines
            )

        ui.sync_ui()
        ctrl.sync_state()

        embed = ui.make_embed()
        await interaction.response.edit_message(view=ctrl)
        if ui.msg_ref:
            try:
                await ui.msg_ref.edit(embed=embed, view=ui)
            except discord.HTTPException as err:
                logger.error("Error updating forfeit message: %s", err)


class ActionControl(View):
    def __init__(self, ui: "UiBoard"):
        super().__init__(timeout=600)
        self.ui = ui
        self.toggle_btn = ToggleModeButton()
        self.quit_btn = QuitButton()
        self.add_item(self.toggle_btn)
        self.add_item(self.quit_btn)

    def sync_state(self):
        if self.ui.board.game_over:
            self.toggle_btn.disabled = True
            self.quit_btn.disabled = True


class UiBoard(View):
    def __init__(self, board: Minefield, user_id: int, username: str, stats_mgr: StatsManager):
        super().__init__(timeout=600)
        self.board = board
        self.user_id = user_id
        self.username = username
        self.stats_mgr = stats_mgr
        self.mode = "reveal"
        self.stats_saved = False
        self.msg_ref: discord.Message | None = None
        self.action_view: ActionControl | None = None

        self.buttons: dict[tuple[int, int], GridButton] = {}
        self._init_grid()

    def _init_grid(self):
        for r in range(5):
            for c in range(5):
                btn = GridButton(row=r, col=c)
                self.buttons[(r, c)] = btn
                self.add_item(btn)

    def sync_ui(self):
        for (r, c), btn in self.buttons.items():
            cell = self.board.grid[r][c]
            btn.emoji = None
            
            if cell.is_revealed:
                btn.disabled = True
                if cell.is_mine:
                    btn.style = ButtonStyle.danger
                    btn.label = "💣"
                elif cell.neighbor_mines > 0:
                    btn.style = ButtonStyle.success
                    btn.label = str(cell.neighbor_mines)
                else:
                    btn.style = ButtonStyle.secondary
                    btn.label = "⬛"
            elif cell.is_flagged:
                btn.disabled = False
                btn.style = ButtonStyle.primary
                btn.label = "🚩"
            else:
                btn.disabled = self.board.game_over
                btn.style = ButtonStyle.secondary
                btn.label = "❓"

    def make_embed(self) -> discord.Embed:
        if self.board.game_over:
            if self.board.won:
                color = discord.Color.green()
                title = "Minesweeper — Victory!"
                desc = f"GG {self.username}! You cleared all the mines."
            else:
                color = discord.Color.red()
                title = "Minesweeper — Game Over"
                desc = f"BOOM! You hit a mine, {self.username}."
        else:
            color = discord.Color.blue()
            title = "Minesweeper"
            desc = f"Player: **{self.username}** | Mode: **{self.mode.upper()}**"

        embed = discord.Embed(title=title, description=desc, color=color)
        embed.add_field(name="Mines Left", value=f"`{self.board.flags_remaining}` / `{self.board.mines}`", inline=True)
        embed.add_field(name="Safe Tiles Remaining", value=f"`{self.board.safe_left}`", inline=True)
        embed.add_field(name="Time", value=f"`{self.board.time_taken()}s`", inline=True)
        return embed

