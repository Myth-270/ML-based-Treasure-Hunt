# treasure_hunt_sprites.py
# Enhanced step-by-step Treasure Hunt with sprite-sheet walking animation (loop while moving)
# Place optional spritesheets in ./assets/:
#   - player_sheet.png  (4 rows: up,left,down,right; cols = frames-per-row)
#   - monster_sheet.png (same layout)
# Fallback to pixel sprites if not present.

import pygame, sys, random, math, time
from collections import deque

# ---------- Config ----------
GRID = 8
CELL = 64
MARGIN = 2
WIDTH = GRID * (CELL + MARGIN) + MARGIN
HEIGHT = WIDTH + 96
MINIMAX_DEPTH_TURNS = 2
WALL_DENSITY = 0.18
AUTO_STEP_INTERVAL = 0.5

# Animation
ANIM_FRAME_MS = 150  # ms between sprite frames while moving
MOVE_MS = 200        # ms to slide from one cell to the next

# Colors / palette
BG_TOP = (20, 20, 30)
BG_BOTTOM = (10, 10, 20)
EXPLORE_COLOR = (100, 170, 220)
PATH_COLOR = (60, 140, 200)
TEXT_COLOR = (220, 220, 220)
HIGHLIGHT = (255, 255, 255)

pygame.init()
FONT = pygame.font.SysFont('consolas', 18)
BIG = pygame.font.SysFont('consolas', 26, bold=True)
CLOCK = pygame.time.Clock()

ASSET_PATHS = {
    'player_sheet': 'assets/player_sheet.png',
    'monster_sheet': 'assets/monster_sheet.png',
    'player': 'assets/player.png',
    'monster': 'assets/monster.png',
    'treasure': 'assets/treasure.png',
    'wall': 'assets/wall.png',
    'floor': 'assets/floor.png'
}

# ---------- Utilities ----------
def load_image(path):
    try:
        return pygame.image.load(path).convert_alpha()
    except Exception:
        return None

def make_pixel_sprite(color, shape='square'):
    s = pygame.Surface((32, 32), pygame.SRCALPHA)
    s.fill((0,0,0,0))
    for y in range(0,32,4):
        for x in range(0,32,4):
            pygame.draw.rect(s, color, (x,y,4,4))
    if shape == 'circle':
        pygame.draw.circle(s, (255,255,255,30),(16,16),8,1)
    return s

def slice_spritesheet(img, rows=4, cols=4, out_size=None):
    """Return frames[row][col] as a list of lists. Resize to out_size if given."""
    w, h = img.get_width(), img.get_height()
    frame_w = w // cols
    frame_h = h // rows
    frames = []
    for r in range(rows):
        row = []
        for c in range(cols):
            surf = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
            surf.blit(img, (0,0), (c*frame_w, r*frame_h, frame_w, frame_h))
            if out_size:
                surf = pygame.transform.smoothscale(surf, out_size)
            row.append(surf)
        frames.append(row)
    return frames

# Try load spritesheets; fallback to single image or pixel sprites
PLAYER_SHEET_IMG = load_image(ASSET_PATHS['player_sheet'])
MONSTER_SHEET_IMG = load_image(ASSET_PATHS['monster_sheet'])
PLAYER_IMG = load_image(ASSET_PATHS['player'])
MONSTER_IMG = load_image(ASSET_PATHS['monster'])
TREASURE_IMG = load_image(ASSET_PATHS['treasure'])
WALL_IMG = load_image(ASSET_PATHS['wall'])
FLOOR_IMG = load_image(ASSET_PATHS['floor'])

# Determine desired asset display size (tile inner size)
ASSET_SIZE = (CELL-8, CELL-8)

# Player frames: 4 directions (up, left, down, right)
if PLAYER_SHEET_IMG:
    # estimate columns
    cols = max(1, PLAYER_SHEET_IMG.get_width() // PLAYER_SHEET_IMG.get_height() )
    PLAYER_FRAMES = slice_spritesheet(PLAYER_SHEET_IMG, rows=4, cols=cols, out_size=ASSET_SIZE)
else:
    # fallback: create 4 rows x 4 cols from generated pixel sprite variants
    small = pygame.transform.smoothscale(make_pixel_sprite((80,200,255),'circle'), ASSET_SIZE)
    PLAYER_FRAMES = [[small.copy() for _ in range(4)] for _ in range(4)]

if MONSTER_SHEET_IMG:
    cols_m = max(1, MONSTER_SHEET_IMG.get_width() // MONSTER_SHEET_IMG.get_height())
    MONSTER_FRAMES = slice_spritesheet(MONSTER_SHEET_IMG, rows=4, cols=cols_m, out_size=ASSET_SIZE)
else:
    smallm = pygame.transform.smoothscale(make_pixel_sprite((255,120,80),'circle'), ASSET_SIZE)
    MONSTER_FRAMES = [[smallm.copy() for _ in range(4)] for _ in range(4)]

# Single-frame assets fallback
if TREASURE_IMG:
    TREASURE_IMG = pygame.transform.smoothscale(TREASURE_IMG, ASSET_SIZE)
else:
    TREASURE_IMG = pygame.transform.smoothscale(make_pixel_sprite((230,200,80),'square'), ASSET_SIZE)

if WALL_IMG:
    WALL_IMG = pygame.transform.smoothscale(WALL_IMG, ASSET_SIZE)
else:
    WALL_IMG = pygame.transform.smoothscale(make_pixel_sprite((120,120,120),'square'), ASSET_SIZE)

if FLOOR_IMG:
    FLOOR_IMG = pygame.transform.smoothscale(FLOOR_IMG, ASSET_SIZE)
else:
    FLOOR_IMG = pygame.transform.smoothscale(make_pixel_sprite((40,60,40),'square'), ASSET_SIZE)

# Directions mapping: row indices for player's frame arrays
DIR_TO_ROW = {'up':0, 'left':1, 'down':2, 'right':3}
ROW_TO_DIR = {v:k for k,v in DIR_TO_ROW.items()}

# ---------- Game logic classes ----------
class BFSStepper:
    def __init__(self, grid, start, goal, monster_pos):
        self.grid = grid
        self.start = start
        self.goal = goal
        self.monster_pos = monster_pos
        self.queue = deque([start])
        self.came_from = {start: None}
        self.explored = []
        self.finished = False
        self.found = False
    def step(self):
        if self.finished:
            return 'finished'
        if not self.queue:
            self.finished = True
            self.found = False
            return 'no_path'
        cur = self.queue.popleft()
        if cur == self.goal:
            self.finished = True
            self.found = True
            return 'found'
        for nx, ny in neighbors(cur):
            if (nx, ny) not in self.came_from and self.grid[ny][nx] != 1 and (nx, ny) != self.monster_pos:
                self.came_from[(nx, ny)] = cur
                self.queue.append((nx, ny))
        self.explored.append(cur)
        return 'explored'
    def reconstruct_path(self):
        if not self.found:
            return []
        path = []
        cur = self.goal
        while cur != self.start:
            path.append(cur)
            cur = self.came_from[cur]
        path.reverse()
        return path

def neighbors(pos):
    x,y = pos
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
        nx,ny = x+dx, y+dy
        if 0<=nx<GRID and 0<=ny<GRID:
            yield (nx,ny)

def manhattan(a,b):
    return abs(a[0]-b[0])+abs(a[1]-b[1])

def minimax_decision(grid, monster_pos, player_pos, turns=MINIMAX_DEPTH_TURNS):
    plies = turns * 2
    def eval_state(m_pos,p_pos):
        if m_pos==p_pos: return 10000
        if p_pos==(GRID-1,GRID-1): return -10000
        return (manhattan(p_pos,(GRID-1,GRID-1))*3) - (manhattan(m_pos,p_pos)*4)
    def max_value(m_pos,p_pos,depth):
        if depth==0 or m_pos==p_pos or p_pos==(GRID-1,GRID-1): return (None, eval_state(m_pos,p_pos))
        best, best_val = None, -math.inf
        for mv in neighbors(m_pos):
            if grid[mv[1]][mv[0]]==1: continue
            _, val = min_value(mv,p_pos,depth-1)
            if val>best_val:
                best_val=val; best=mv
        return (best,best_val)
    def min_value(m_pos,p_pos,depth):
        if depth==0 or m_pos==p_pos or p_pos==(GRID-1,GRID-1): return (None, eval_state(m_pos,p_pos))
        best, best_val = None, math.inf
        for mv in neighbors(p_pos):
            if grid[mv[1]][mv[0]]==1: continue
            _, val = max_value(m_pos,mv,depth-1)
            if val<best_val:
                best_val=val; best=mv
        return (best,best_val)
    move,_ = max_value(monster_pos, player_pos, plies)
    if move is None: return monster_pos
    return move

def create_grid():
    grid = [[0 for _ in range(GRID)] for _ in range(GRID)]
    for y in range(GRID):
        for x in range(GRID):
            if random.random() < WALL_DENSITY:
                grid[y][x] = 1
    grid[0][0]=0
    grid[GRID-1][GRID-1]=0
    mid=(GRID//2, GRID//2)
    grid[mid[1]][mid[0]]=0
    return grid

# ---------- Drawing ----------

def draw_background(surface):
    for i in range(HEIGHT):
        r = BG_TOP[0] + (BG_BOTTOM[0]-BG_TOP[0]) * i // HEIGHT
        g = BG_TOP[1] + (BG_BOTTOM[1]-BG_TOP[1]) * i // HEIGHT
        b = BG_TOP[2] + (BG_BOTTOM[2]-BG_TOP[2]) * i // HEIGHT
        pygame.draw.line(surface, (r,g,b), (0,i), (WIDTH, i))

def cell_rect(x,y):
    px = MARGIN + x*(CELL+MARGIN)
    py = MARGIN + y*(CELL+MARGIN)
    return pygame.Rect(px, py, CELL, CELL)

def draw_grid(surface, grid, explored, path, player_draw_pos, monster_draw_pos, treasure_pos, info_lines, thinking=False):
    draw_background(surface)
    # tiles
    for y in range(GRID):
        for x in range(GRID):
            rect = cell_rect(x,y)
            surface.blit(FLOOR_IMG, (rect.x+4, rect.y+4))
            if grid[y][x]==1:
                surface.blit(WALL_IMG, (rect.x+4, rect.y+4))
            if (x,y) in explored:
                s = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                s.fill((*EXPLORE_COLOR, 100))
                surface.blit(s, (rect.x, rect.y))
    # path line (from player grid center through path)
    if path:
        pts = [((p[0]*(CELL+MARGIN)+MARGIN + CELL//2), (p[1]*(CELL+MARGIN)+MARGIN + CELL//2)) for p in [player_draw_pos['grid']] + path]
        if len(pts)>=2:
            pygame.draw.lines(surface, PATH_COLOR, False, pts, 4)
    # treasure (stationary)
    tx,ty = treasure_pos
    trect = cell_rect(tx,ty)
    surface.blit(TREASURE_IMG, (trect.x+4, trect.y+4))
    # player (interpolated pos) - player_draw_pos contains pixel pos and direction/frame index
    px,py = player_draw_pos['pixel']
    prow = DIR_TO_ROW[player_draw_pos['dir']]
    pframe = player_draw_pos['frame']
    p_surf = PLAYER_FRAMES[prow][pframe]
    surface.blit(p_surf, (px+4, py+4))
    # monster
    mx,my = monster_draw_pos['pixel']
    mrow = DIR_TO_ROW[monster_draw_pos['dir']]
    mframe = monster_draw_pos['frame']
    m_surf = MONSTER_FRAMES[mrow][mframe]
    surface.blit(m_surf, (mx+4, my+4))
    # info panel
    panel_y = WIDTH + 8
    for i, line in enumerate(info_lines):
        txt = FONT.render(line, True, TEXT_COLOR)
        surface.blit(txt, (8, panel_y + i*20))
    # thinking bubble
    if thinking:
        mrect = cell_rect(monster_draw_pos['grid'][0], monster_draw_pos['grid'][1])
        bx = mrect.x + CELL//2
        by = mrect.y - 18
        bubble = FONT.render('Thinking...', True, HIGHLIGHT)
        surface.blit(bubble, (bx - bubble.get_width()//2, by - bubble.get_height()))

# ---------- Interpolation & animation handler ----------
def grid_to_pixel(cell):
    x,y = cell
    px = MARGIN + x*(CELL+MARGIN)
    py = MARGIN + y*(CELL+MARGIN)
    return (px, py)

def start_move(entity_draw, from_cell, to_cell):
    entity_draw['grid'] = to_cell
    entity_draw['from_grid'] = from_cell
    entity_draw['to_grid'] = to_cell
    entity_draw['move_start'] = time.time()
    entity_draw['moving'] = True
    # set direction row based on vector
    dx = to_cell[0] - from_cell[0]
    dy = to_cell[1] - from_cell[1]
    if dx==1: entity_draw['dir'] = 'right'
    elif dx==-1: entity_draw['dir'] = 'left'
    elif dy==1: entity_draw['dir'] = 'down'
    elif dy==-1: entity_draw['dir'] = 'up'
    entity_draw['frame_timer'] = 0

def update_entity_draw(entity_draw, dt_ms):
    # animation frame stepping
    if entity_draw['moving']:
        entity_draw['frame_timer'] += dt_ms
        frames_count = len(PLAYER_FRAMES[0])
        if entity_draw['frame_timer'] >= ANIM_FRAME_MS:
            entity_draw['frame_timer'] -= ANIM_FRAME_MS
            entity_draw['frame'] = (entity_draw['frame'] + 1) % frames_count
        # interpolation progress
        elapsed = (time.time() - entity_draw['move_start']) * 1000.0
        t = min(1.0, elapsed / MOVE_MS)
        fx = (entity_draw['to_grid'][0] * (CELL+MARGIN) + MARGIN)
        fy = (entity_draw['to_grid'][1] * (CELL+MARGIN) + MARGIN)
        sx = (entity_draw['from_grid'][0] * (CELL+MARGIN) + MARGIN)
        sy = (entity_draw['from_grid'][1] * (CELL+MARGIN) + MARGIN)
        curx = sx + (fx - sx) * t
        cury = sy + (fy - sy) * t
        entity_draw['pixel'] = (curx, cury)
        if t>=1.0:
            entity_draw['moving'] = False
            entity_draw['frame'] = 0  # return to idle frame 0
    else:
        entity_draw['frame_timer'] = 0
        entity_draw['frame'] = 0
        # ensure pixel matches grid
        gx,gy = entity_draw['grid']
        entity_draw['pixel'] = (MARGIN + gx*(CELL+MARGIN), MARGIN + gy*(CELL+MARGIN))

# ---------- Main ----------
def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Treasure Hunt: BFS (step) vs Minimax (retro sprites)')
    grid = create_grid()
    player_grid = (0,0)
    monster_grid = (GRID//2, GRID//2)
    treasure_grid = (GRID-1, GRID-1)

    bfs = BFSStepper(grid, player_grid, treasure_grid, monster_grid)
    path = []
    explored = []

    # draw state for player & monster (handles animation)
    player_draw = {'grid': player_grid, 'pixel': grid_to_pixel(player_grid), 'frame':0, 'dir':'down',
                   'moving':False, 'from_grid':player_grid, 'to_grid':player_grid, 'move_start':0, 'frame_timer':0}
    monster_draw = {'grid': monster_grid, 'pixel': grid_to_pixel(monster_grid), 'frame':0, 'dir':'up',
                    'moving':False, 'from_grid':monster_grid, 'to_grid':monster_grid, 'move_start':0, 'frame_timer':0}

    running = True
    state = 'start'
    status = 'Press SPACE to start.  N = next step.  R = restart.  A = toggle auto.'
    auto = False
    last_auto = 0
    auto_interval = AUTO_STEP_INTERVAL

    while running:
        dt = CLOCK.tick(60)
        now = time.time()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False
                elif e.key == pygame.K_SPACE and state == 'start':
                    state = 'exploring'
                    status = 'Exploring (BFS). Press N to step.'
                elif e.key == pygame.K_r:
                    grid = create_grid()
                    player_grid = (0,0)
                    monster_grid = (GRID//2, GRID//2)
                    treasure_grid = (GRID-1, GRID-1)
                    bfs = BFSStepper(grid, player_grid, treasure_grid, monster_grid)
                    path = []
                    explored = []
                    player_draw.update({'grid':player_grid, 'pixel':grid_to_pixel(player_grid), 'frame':0, 'dir':'down','moving':False,'from_grid':player_grid,'to_grid':player_grid})
                    monster_draw.update({'grid':monster_grid, 'pixel':grid_to_pixel(monster_grid), 'frame':0, 'dir':'up','moving':False,'from_grid':monster_grid,'to_grid':monster_grid})
                    state = 'start'
                    status = 'Press SPACE to start.  N = next step.  R = restart.  A = toggle auto.'
                    auto = False
                elif e.key == pygame.K_n:
                    # advance step machine
                    if state == 'start':
                        state = 'exploring'
                        status = 'Exploring (BFS). Press N to step.'
                    elif state == 'exploring':
                        res = bfs.step()
                        explored = list(bfs.explored)
                        if res == 'found':
                            path = bfs.reconstruct_path()
                            state = 'path_ready'
                            status = 'Path found. Press N to move player one step.'
                        elif res == 'no_path':
                            status = 'No path. Game over. Red wins. Press R to restart.'
                            state = 'game_over'
                    elif state == 'path_ready':
                        if path:
                            # move player one step (start anim)
                            next_cell = path.pop(0)
                            start_move(player_draw, player_draw['grid'], next_cell)
                            player_grid = next_cell
                        # check
                        if player_grid == treasure_grid:
                            status = 'Blue (BFS) reached treasure! You win! Press R to restart.'
                            state = 'game_over'
                        elif player_grid == monster_grid:
                            status = 'Monster caught player! Red wins! Press R to restart.'
                            state = 'game_over'
                        else:
                            state = 'monster_moving'
                            status = 'Monster thinking... Press N to let monster move.'
                    elif state == 'monster_moving':
                        # minimax & move monster
                        move = minimax_decision(grid, monster_grid, player_grid, turns=MINIMAX_DEPTH_TURNS)
                        start_move(monster_draw, monster_draw['grid'], move)
                        monster_grid = move
                        if monster_grid == player_grid:
                            status = 'Monster caught player! Red wins! Press R to restart.'
                            state = 'game_over'
                        else:
                            # restart BFS from new player position
                            bfs = BFSStepper(grid, player_grid, treasure_grid, monster_grid)
                            path = []
                            explored = []
                            state = 'exploring'
                            status = 'Exploring (BFS). Press N to step.'
                elif e.key == pygame.K_a:
                    auto = not auto
                    status = 'Auto: ON' if auto else 'Auto: OFF'
                elif e.key == pygame.K_PLUS or e.key == pygame.K_EQUALS:
                    auto_interval = max(0.05, auto_interval - 0.1)
                elif e.key == pygame.K_MINUS:
                    auto_interval += 0.1

        # auto stepping
        if auto and state not in ('start','game_over'):
            if now - last_auto > auto_interval:
                pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_n}))
                last_auto = now

        # update animations (player and monster)
        update_entity_draw(player_draw, dt)
        update_entity_draw(monster_draw, dt)

        # Draw UI
        info = [
            f'State: {state}',
            f'Steps explored: {len(explored):>3}',
            f'Path length: {len(path):>3}',
            f'Auto: {"ON" if auto else "OFF"} (interval {auto_interval:.2f}s)'
        ]
        thinking = (state == 'monster_moving')
        draw_grid(screen, grid, explored, path, player_draw, monster_draw, treasure_grid, info, thinking=thinking)

        # Top / bottom clean overlay with fixed spacing
        if state == 'start':
            title = BIG.render('Treasure Hunt: BFS (step) vs Minimax (retro sprites)', True, TEXT_COLOR)
            screen.blit(title, (8, WIDTH + 8))
            inst = FONT.render('Press SPACE to start.   N = next step.   R = restart.   A = auto.   +/- speed', True, TEXT_COLOR)
            screen.blit(inst, (8, WIDTH + 40))
        else:
            status_surf = FONT.render(status, True, TEXT_COLOR)
            screen.blit(status_surf, (8, WIDTH + 8))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
