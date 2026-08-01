import json
import os
import logging
from typing import Any

logger = logging.getLogger("minesweeper")
STATS_FILE = "stats.json"

class StatsManager:
    def __init__(self, path: str = STATS_FILE):
        self.path = path
        self.db: dict[str, dict[str, Any]] = self._load()

    def _load(self) -> dict[str, dict[str, Any]]:
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as err:
            logger.error("Could not read stats file (%s): %s", self.path, err)
            return {}

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.db, f, indent=2)
        except Exception as err:
            logger.error("Could not write to stats file (%s): %s", self.path, err)

    def get_user_stats(self, user_id: int) -> dict[str, Any]:
        uid = str(user_id)
        if uid not in self.db:
            return {
                "games_played": 0,
                "wins": 0,
                "losses": 0,
                "mines_cleared": 0,
                "best_times": {}
            }
        return self.db[uid]

    def record_game(self, user_id: int, won: bool, elapsed_seconds: int, mines_count: int, tag: str = "5x5"):
        uid = str(user_id)
        if uid not in self.db:
            self.db[uid] = {
                "games_played": 0,
                "wins": 0,
                "losses": 0,
                "mines_cleared": 0,
                "best_times": {}
            }

        user_data = self.db[uid]
        user_data["games_played"] += 1
        
        if won:
            user_data["wins"] += 1
            user_data["mines_cleared"] += mines_count
            best = user_data["best_times"].get(tag)
            if best is None or elapsed_seconds < best:
                user_data["best_times"][tag] = elapsed_seconds
        else:
            user_data["losses"] += 1

        self._save()

    def get_leaderboard(self, category: str = "wins", limit: int = 10) -> list[dict[str, Any]]:
        rankings = []
        for uid, user_data in self.db.items():
            total = user_data.get("games_played", 0)
            wins = user_data.get("wins", 0)
            win_rate = (wins / total * 100) if total > 0 else 0.0
            
            rankings.append({
                "user_id": int(uid),
                "games_played": total,
                "wins": wins,
                "losses": user_data.get("losses", 0),
                "win_rate": round(win_rate, 1),
                "mines_cleared": user_data.get("mines_cleared", 0),
            })

        if category == "win_rate":
            rankings.sort(key=lambda x: (x["win_rate"], x["wins"]), reverse=True)
        else:
            rankings.sort(key=lambda x: (x["wins"], x["win_rate"]), reverse=True)

        return rankings[:limit]

