# 🗺️ ML-based Treasure Hunt

A grid-based treasure hunt game built with Python and Pygame, where an AI agent navigates an obstacle-filled maze to find treasure while being hunted by a monster. The player uses **BFS (Breadth-First Search)** to pathfind, while the monster uses **Minimax** to make adversarial decisions.

---

## 🎮 Gameplay Overview

- The game takes place on an **8×8 grid** filled with walls, open floors, a player, a monster, and a treasure.
- The **player (blue)** uses BFS to find the shortest path to the treasure.
- The **monster (red)** uses Minimax to chase the player intelligently.
- You can step through the search process manually or let it run automatically.

---

## 🧠 Algorithms Used

### Breadth-First Search (BFS)
Used by the player to explore the grid step-by-step and find the shortest path to the treasure. The exploration is animated — you can watch BFS expand cell by cell before committing to a path.

### Minimax
Used by the monster to decide its next move. The monster evaluates future game states up to a configurable depth and picks the move most likely to intercept the player.

---

## 📁 File Structure

| File | Description |
|------|-------------|
| `AIML.py` | Original version of the game |
| `AIML_fixed.py` | Bug-fixed version |
| `AIML_fixed_debug.py` | Version with debug output |
| `AIML_fixed_debug_fixed3.py` | Latest stable version with smooth animations |
| `floor.png` | Floor tile sprite |
| `wall.png` | Wall tile sprite |
| `treasure.png` | Treasure sprite |
| `h.png` | Player sprite sheet |
| `hmonster_sheet.png` | Monster sprite sheet |

> **Run the latest version:** `AIML_fixed_debug_fixed3.py`

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Pygame

### Installation

```bash
git clone https://github.com/Myth-270/ML-based-Treasure-Hunt.git
cd ML-based-Treasure-Hunt
pip install pygame
```

### Running the Game

```bash
python AIML_fixed_debug_fixed3.py
```

---

## 🕹️ Controls

| Key | Action |
|-----|--------|
| `SPACE` | Start the game |
| `N` | Step forward (explore one BFS node / move one step) |
| `A` | Toggle auto-play mode |
| `+` / `-` | Increase / decrease auto-play speed |
| `R` | Restart with a new random map |
| `ESC` | Quit |

---

## ⚙️ Configuration

You can tweak these constants at the top of the script:

| Constant | Default | Description |
|----------|---------|-------------|
| `GRID` | `8` | Grid size (N×N) |
| `CELL` | `64` | Cell size in pixels |
| `WALL_DENSITY` | `0.18` | Probability of a cell being a wall |
| `MINIMAX_DEPTH_TURNS` | `2` | Look-ahead depth for the monster's Minimax |
| `AUTO_STEP_INTERVAL` | `0.5` | Seconds between auto-steps |

---

## 🖼️ Game States

1. **Start** — Press `SPACE` or `N` to begin.
2. **Exploring** — BFS expands across the grid (highlighted in blue).
3. **Path Ready** — Shortest path found; player moves step by step.
4. **Monster Moving** — Monster uses Minimax to take its turn.
5. **Game Over** — Either the player reaches the treasure (player wins) or the monster catches the player (monster wins). Press `R` to restart.

---

## 📊 HUD Info

The bottom panel displays live game info:
- Current status message
- Game state
- Number of BFS steps explored
- Remaining path length
- Auto-play status and speed

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
