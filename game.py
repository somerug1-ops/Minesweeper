import random
import time
import logging

logger = logging.getLogger("minesweeper")

NUMBERS = {0: "0️⃣", 1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣", 6: "6️⃣", 7: "7️⃣", 8: "8️⃣"}
MINE_EMOJI = "💣"
FLAG_EMOJI = "🚩"

class Cell:
    def __init__(self):
        self.is_mine = False
        self.neighbor_mines = 0
        self.is_revealed = False
        self.is_flagged = False

class Minefield:
    def __init__(self, rows: int = 5, cols: int = 5, mines: int = 5):
        self.rows = max(2, min(rows, 12))
        self.cols = max(2, min(cols, 12))
        self.mines = min(mines, (self.rows * self.cols) - 1)
        self.grid = [[Cell() for _ in range(self.cols)] for _ in range(self.rows)]
        self.initialized = False
        self.game_over = False
        self.won = False
        self.start_time = time.time()
        self.end_time = None
        self.safe_left = (self.rows * self.cols) - self.mines

    def setup_mines(self, safe_r: int, safe_c: int):
        placed = 0
        while placed < self.mines:
            r = random.randint(0, self.rows - 1)
            c = random.randint(0, self.cols - 1)
            if (r, c) == (safe_r, safe_c) or self.grid[r][c].is_mine:
                continue
            self.grid[r][c].is_mine = True
            placed += 1

        # Calculate numbers for adjacent mines
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.grid[r][c].is_mine:
                    count = 0
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                                if self.grid[nr][nc].is_mine:
                                    count += 1
                    self.grid[r][c].neighbor_mines = count

        self.initialized = True

    def step(self, r: int, c: int) -> str:
        if self.game_over:
            return "GAME_OVER"

        if not (0 <= r < self.rows and 0 <= c < self.cols):
            return "OUT_OF_BOUNDS"

        target = self.grid[r][c]
        if target.is_revealed or target.is_flagged:
            return "NOOP"

        # Generate board after first click so player never hits a mine on turn 1
        if not self.initialized:
            self.setup_mines(r, c)

        if target.is_mine:
            target.is_revealed = True
            self.game_over = True
            self.won = False
            self.end_time = time.time()
            # Reveal all mines on lose
            for row in self.grid:
                for cell in row:
                    if cell.is_mine:
                        cell.is_revealed = True
            return "MINE"

        # Auto-reveal adjacent empty tiles
        stack = [(r, c)]
        visited = set()

        while stack:
            curr_r, curr_c = stack.pop()
            if (curr_r, curr_c) in visited:
                continue
            visited.add((curr_r, curr_c))

            cell = self.grid[curr_r][curr_c]
            if cell.is_flagged or cell.is_mine:
                continue

            if not cell.is_revealed:
                cell.is_revealed = True
                self.safe_left -= 1

            if cell.neighbor_mines == 0:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = curr_r + dr, curr_c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            adj = self.grid[nr][nc]
                            if not adj.is_revealed and not adj.is_flagged:
                                stack.append((nr, nc))

        if self.safe_left <= 0:
            self.game_over = True
            self.won = True
            self.end_time = time.time()
            # Flag remaining mines on win
            for row in self.grid:
                for cell in row:
                    if cell.is_mine:
                        cell.is_flagged = True
            return "WIN"

        return "OK"

    def flag(self, r: int, c: int) -> bool:
        if self.game_over or not (0 <= r < self.rows and 0 <= c < self.cols):
            return False

        cell = self.grid[r][c]
        if cell.is_revealed:
            return False

        cell.is_flagged = not cell.is_flagged
        return True

    @property
    def flags_remaining(self) -> int:
        flagged = sum(1 for row in self.grid for cell in row if cell.is_flagged)
        return self.mines - flagged

    def time_taken(self) -> int:
        end = self.end_time or time.time()
        return int(end - self.start_time)

    def to_spoilers(self) -> str:
        if not self.initialized:
            self.setup_mines(self.rows // 2, self.cols // 2)

        lines = []
        for r in range(self.rows):
            row_str = ""
            for c in range(self.cols):
                cell = self.grid[r][c]
                if cell.is_mine:
                    row_str += f"||{MINE_EMOJI}||"
                else:
                    row_str += f"||{NUMBERS.get(cell.neighbor_mines, '0️⃣')}||"
            lines.append(row_str)
        return "\n".join(lines)

