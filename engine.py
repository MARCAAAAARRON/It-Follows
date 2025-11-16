import random
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.event import EventDispatcher
from kivy.uix.screenmanager import NoTransition
from constants import *

class GameEngine(EventDispatcher):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.WIDTH = int(ui.ids.gamecanvas.width) if 'gamecanvas' in ui.ids else Window.width
        self.HEIGHT = int(ui.ids.gamecanvas.height) if 'gamecanvas' in ui.ids else int(Window.height * GAME_SCREEN_HEIGHT_RATIO)
        self.cols = max(3, self.WIDTH // TILE_SIZE)
        self.rows = max(3, int(self.HEIGHT // TILE_SIZE))
        self.player = [TILE_SIZE, TILE_SIZE, PLAYER_SIZE, PLAYER_SIZE]
        self.goal = [max(TILE_SIZE, self.WIDTH - 2*TILE_SIZE), max(TILE_SIZE, self.HEIGHT - 2*TILE_SIZE), GOAL_SIZE, GOAL_SIZE]
        self.enemy = None
        self.item = None
        self.key = None
        self.journal = None
        self.lever = None
        self.archive = None
        self.lever_puzzle = []
        self.correct_lever = -1
        self.survivor = None
        self.survivor_heeded = False
        self.memory_discovered = False
        self.l4_mode = None
        self.enemy_frozen_until = 0.0
        self.torch_drain_mult = 1.0
        self.level = 1
        self.lives = 3
        self.enemy_speed = BASE_ENEMY_SPEED
        self.speed = PLAYER_SPEED
        self.echo_uses = INITIAL_ECHO_USES
        self.echo_duration = ECHO_DURATION
        self.echo_time = -10.0
        self.enemy_active = False
        self.key_collected = False
        self.timer = 0.0
        self.torch_battery = INITIAL_TORCH_BATTERY
        self.drain_active = 0.0
        self.drain_idle = 0.0
        self.enemy_multiplier = 1.0
        self.input_dir = [0, 0]
        self._ev = None
        self.register_event_type('on_show_overlay')
        self.register_event_type('on_hide_overlay')
        self.register_event_type('on_update_ui')
        self.reset_level()

    def on_show_overlay(self, mode, text, btns):
        pass

    def on_hide_overlay(self):
        pass

    def on_update_ui(self, night_text, light_text, time_text, lives_text):
        pass

    def apply_difficulty(self, da, di, em):
        self.drain_active = da
        self.drain_idle = di
        self.enemy_multiplier = em
        self.enemy_speed = (BASE_ENEMY_SPEED + ENEMY_SPEED_LEVEL_MULTIPLIER * (self.level - 1)) * self.enemy_multiplier

    def start(self):
        self._ev = Clock.schedule_interval(self.update, UPDATE_RATE)

    def stop(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None

    def make_rect(self):
        cx = random.randint(1, max(1, self.cols-2))
        cy = random.randint(1, max(1, self.rows-2))
        x = cx * TILE_SIZE
        y = cy * TILE_SIZE
        return [x, y, TILE_SIZE-10, TILE_SIZE-10]

    def make_open_rect(self):
        # Find a random open cell (maze==0) within bounds
        for _ in range(500):
            cx = random.randint(1, max(1, self.cols-2))
            cy = random.randint(1, max(1, self.rows-2))
            if 0 <= cy < len(self.maze) and 0 <= cx < len(self.maze[0]) and self.maze[cy][cx] == 0:
                return [cx * TILE_SIZE, cy * TILE_SIZE, TILE_SIZE-10, TILE_SIZE-10]
        # Fallback to any rect if none found (very dense mazes)
        return self.make_rect()

    def generate_maze(self, density=INITIAL_MAZE_DENSITY):
        maze = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        for y in range(self.rows):
            for x in range(self.cols):
                if random.random() < density and (x, y) not in [(1, 1), (self.cols-2, self.rows-2)]:
                    maze[y][x] = 1
        return maze

    def generate_test_chamber(self):
        maze = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        for x in range(self.cols):
            maze[0][x] = 1
            maze[self.rows - 1][x] = 1
        for y in range(self.rows):
            maze[y][0] = 1
            maze[y][self.cols - 1] = 1
        for x in range(2, self.cols - 2):
            if x % 4 != 0:
                maze[self.rows // 2][x] = 1
        for y in range(2, self.rows - 2):
            if y % 3 == 0:
                maze[y][self.cols // 2] = 1
        maze[1][1] = 0
        maze[self.rows - 2][self.cols - 2] = 0
        return maze

    def reset_level(self):
        self.cols = max(3, self.WIDTH // TILE_SIZE)
        self.rows = max(3, int(self.HEIGHT // TILE_SIZE))
        if self.level == 9:
            self.maze = self.generate_test_chamber()
        else:
            density = min(INITIAL_MAZE_DENSITY + MAZE_DENSITY_LEVEL_MULTIPLIER * (self.level - 1), MAX_MAZE_DENSITY)
            self.maze = self.generate_maze(density)
        self.player[0], self.player[1] = TILE_SIZE, TILE_SIZE
        self.enemy = self.make_open_rect()
        self.item = self.make_open_rect()
        # Gated key: only spawn immediately on non-gated levels
        gated_levels = {2, 3, 4, 6, 7}
        self.key = None if self.level in gated_levels else self.make_open_rect()
        self.goal = [max(TILE_SIZE, self.WIDTH - 2*TILE_SIZE), max(TILE_SIZE, self.HEIGHT - 2*TILE_SIZE), GOAL_SIZE, GOAL_SIZE]
        self.journal = None
        self.lever = None
        self.archive = None
        self.lever_puzzle = []
        self.correct_lever = -1
        self.survivor = None
        self.survivor_heeded = False
        self.memory_discovered = False
        self.l4_mode = None
        self.enemy_frozen_until = 0.0
        self.torch_drain_mult = 1.0
        self.key_collected = False
        self.enemy_active = False
        self.echo_uses = INITIAL_ECHO_USES
        self.echo_time = -10.0
        self.timer = 0.0
        self.enemy_speed = (BASE_ENEMY_SPEED + ENEMY_SPEED_LEVEL_MULTIPLIER * (self.level - 1)) * self.enemy_multiplier
        lives_text = "Lives: ∞" if self.lives == -1 else f"Lives: {self.lives}"
        self.dispatch('on_update_ui', f"Night {self.level}/{MAX_LEVELS}", f"Light: {self.echo_uses}", f"Time: {int(self.timer)}", lives_text)
        if self.level == 2:
            self.journal = self.make_open_rect()
        if self.level == 3:
            self.lever = self.make_open_rect()
        if self.level == 4:
            self.journal = self.make_open_rect()
        if self.level == 6:
            self.archive = self.make_open_rect()
            self.torch_drain_mult = TORCH_DRAIN_MULTIPLIER_LEVEL_6
        if self.level == 7:
            self.survivor = self.make_open_rect()
        if self.level == 8:
            self.lever_puzzle = [self.make_open_rect() for _ in range(10)]
            base = 3 if self.memory_discovered else 7
            self.correct_lever = (base + (1 if not self.survivor_heeded else -1)) % 10

    def set_canvas_size(self, width, height):
        new_w = int(max(1, width))
        new_h = int(max(1, height))
        new_cols = max(3, new_w // TILE_SIZE)
        new_rows = max(3, int(new_h // TILE_SIZE))
        if self.WIDTH == new_w and self.HEIGHT == new_h and self.cols == new_cols and self.rows == new_rows:
            return
        self.WIDTH = new_w
        self.HEIGHT = new_h
        # Only regenerate the level if grid dimensions actually changed to avoid IndexError
        dims_changed = (new_cols != self.cols) or (new_rows != self.rows)
        self.cols, self.rows = new_cols, new_rows
        if dims_changed:
            self.reset_level()
        else:
            self.goal[0] = min(self.goal[0], max(TILE_SIZE, self.WIDTH - 2*TILE_SIZE))
            self.goal[1] = min(self.goal[1], max(TILE_SIZE, self.HEIGHT - 2*TILE_SIZE))

    def rects_collide(self, a, b):
        if a is None or b is None:
            return False
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        return (ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by)

    def collides_walls(self, r):
        x, y, w, h = r
        rows = len(self.maze)
        cols = len(self.maze[0]) if rows else 0
        for yy in range(rows):
            for xx in range(cols):
                if self.maze[yy][xx] == 1:
                    rx, ry, rw, rh = xx*TILE_SIZE, yy*TILE_SIZE, TILE_SIZE, TILE_SIZE
                    if (x < rx + rw and x + w > rx and y < ry + rh and y + h > ry):
                        return True
        return False

    def use_light(self):
        if self.echo_uses > 0:
            self.echo_time = self.timer
            self.echo_uses -= 1
            self.enemy_active = True
            lives_text = "Lives: ∞" if self.lives == -1 else f"Lives: {self.lives}"
            self.dispatch('on_update_ui', f"Night {self.level}/{MAX_LEVELS}", f"Light: {self.echo_uses}", f"Time: {int(self.timer)}", lives_text)

    def update(self, dt):
        self._update_timers(dt)
        self._update_player_movement()
        self._update_enemy_ai()
        self._check_collisions()
        self._handle_story_events()
        echo_active = (self.timer - self.echo_time) < self.echo_duration
        self.draw(echo_active)
        lives_text = "Lives: ∞" if self.lives == -1 else f"Lives: {self.lives}"
        self.dispatch('on_update_ui', f"Night {self.level}/{MAX_LEVELS}", f"Light: {self.echo_uses}", f"Time: {int(self.timer)}", lives_text)

    def _update_timers(self, dt):
        self.timer += dt
        drain = self.drain_active if (self.timer - self.echo_time) < self.echo_duration else self.drain_idle
        self.torch_battery = max(0.0, self.torch_battery - (drain * self.torch_drain_mult * dt))
        if self.torch_battery <= 0 and (self.timer - self.echo_time) < self.echo_duration:
            self.echo_time = -10.0

    def _update_player_movement(self):
        move_vec = [self.input_dir[0] * self.speed, self.input_dir[1] * self.speed]
        new_rect = [
            self.player[0] + move_vec[0],
            self.player[1] + move_vec[1],
            self.player[2],
            self.player[3]
        ]
        if not self.collides_walls(new_rect):
            self.player = new_rect

    def _update_enemy_ai(self):
        echo_active = (self.timer - self.echo_time) < self.echo_duration
        if self.enemy_active and not echo_active and self.timer >= self.enemy_frozen_until:
            ex, ey = self.enemy[0], self.enemy[1]
            px, py = self.player[0], self.player[1]
            dx, dy = px - ex, py - ey
            length = max(1.0, (dx*dx + dy*dy)**0.5)
            ex += (dx/length) * self.enemy_speed
            ey += (dy/length) * self.enemy_speed
            self.enemy[0], self.enemy[1] = ex, ey

    def _check_collisions(self):
        if not self.key_collected and self.rects_collide(self.player, self.key):
            self.key_collected = True
            self.dispatch('on_show_overlay', "story", "Gate Unlocked!", ["OK"])
        if self.rects_collide(self.player, self.item):
            self.echo_uses += 1
            lives_text = "Lives: ∞" if self.lives == -1 else f"Lives: {self.lives}"
            self.dispatch('on_update_ui', f"Night {self.level}/{MAX_LEVELS}", f"Light: {self.echo_uses}", f"Time: {int(self.timer)}", lives_text)
            self.item = self.make_rect()
            self.enemy_frozen_until = self.timer + 2.0
            self.dispatch('on_show_overlay', "story", "The shadow hesitates...", ["OK"])
        if self.journal and self.rects_collide(self.player, self.journal):
            self.journal = None
            if self.level == 2:
                self.dispatch('on_show_overlay', "journal", "Journal: Project Umbra—light reveals, shadow consumes.", ["OK"])
                if self.key is None:
                    self.key = self.make_open_rect()
                    self.dispatch('on_show_overlay', "story", "A key has appeared.", ["OK"])
            elif self.level == 4:
                self.dispatch('on_show_overlay', "journal", "Journal: Subjects report a presence when light fails.", ["OK"])
                if self.key is None:
                    self.key = self.make_open_rect()
                    self.dispatch('on_show_overlay', "story", "A key has appeared.", ["OK"])
        if self.lever and self.rects_collide(self.player, self.lever):
            self.lever = None
            self.memory_discovered = True
            self.dispatch('on_show_overlay', "story", "Memory: You built this. The maze was your experiment.", ["OK"])
            if self.key is None:
                self.key = self.make_open_rect()
                self.dispatch('on_show_overlay', "story", "A key has appeared.", ["OK"])
        if self.archive and self.rects_collide(self.player, self.archive):
            self.archive = None
            self.memory_discovered = True
            self.dispatch('on_show_overlay', "story", "Archive: Lead: Eli. Trials escalated. One subject lost.", ["OK"])
            if self.key is None:
                self.key = self.make_open_rect()
                self.dispatch('on_show_overlay', "story", "A key has appeared.", ["OK"])
        if self.survivor and self.rects_collide(self.player, self.survivor):
            self.survivor = None
            self.dispatch('on_show_overlay', "survivor", "A survivor begs: 'Don't pull the final lever.'", ["Heed", "Ignore"])
            if self.key is None:
                self.key = self.make_open_rect()
                self.dispatch('on_show_overlay', "story", "A key has appeared.", ["OK"])
        if self.level == 8 and self.lever_puzzle:
            for i, r in enumerate(list(self.lever_puzzle)):
                if self.rects_collide(self.player, r):
                    if i == self.correct_lever:
                        self.key_collected = True
                        self.dispatch('on_show_overlay', "story", "The gate hums open.", ["OK"])
                    else:
                        self.lever_puzzle.pop(i)
                        self.enemy_speed *= ENEMY_SPEED_WRONG_LEVER_MULTIPLIER
                        self.dispatch('on_show_overlay', "story", "Wrong lever. The shadow stirs...", ["OK"])
                    break
        if self.rects_collide(self.player, self.enemy):
            if self.ui.overlay_visible == 0:
                if self.lives == -1:
                    msg = "You have been caught by the shadow!"
                else:
                    left = max(0, self.lives - 1)
                    msg = f"You have been caught by the shadow! Lives left: {left}"
                self.dispatch('on_show_overlay', "story", msg, ["OK"])
            return
        if self.key_collected and self.rects_collide(self.player, self.goal):
            if self.level < MAX_LEVELS:
                if self.level == 5:
                    self.dispatch('on_show_overlay', "riddle", "Riddle: What follows but never leads?", ["Submit"])
                else:
                    self.level += 1
                    self.reset_level()
            else:
                self.dispatch('on_show_overlay', "endings", "Act III: Escape or Embrace", ["Escape", "Stay", "Destroy", "Merge"])
                return

    def _handle_story_events(self):
        if self.level == 4 and self.l4_mode is None and self.ui.overlay_visible == 0:
            self.dispatch('on_show_overlay', "l4_choice", "Two paths: Safe or Fast?", ["Safe", "Fast"])

    def draw(self, echo_active: bool):
        canvas = self.ui.ids.gamecanvas
        canvas.canvas.clear()
        gx, gy = canvas.pos
        with canvas.canvas:
            Color(*COLOR_BLACK)
            Rectangle(pos=(gx, gy), size=(self.WIDTH, self.HEIGHT))
            if echo_active:
                Color(*COLOR_MAZE_WALL)
                for y in range(self.rows):
                    for x in range(self.cols):
                        if self.maze[y][x] == 1:
                            Rectangle(pos=(gx + x*TILE_SIZE, gy + y*TILE_SIZE), size=(TILE_SIZE, TILE_SIZE))
                if not self.key_collected and self.key:
                    Color(*COLOR_KEY)
                    Rectangle(pos=(gx + self.key[0], gy + self.key[1]), size=(self.key[2], self.key[3]))
                if self.key_collected:
                    Color(*COLOR_GOAL)
                    Rectangle(pos=(gx + self.goal[0], gy + self.goal[1]), size=(self.goal[2], self.goal[3]))
                if self.enemy:
                    Color(*COLOR_ENEMY)
                    Rectangle(pos=(gx + self.enemy[0], gy + self.enemy[1]), size=(self.enemy[2], self.enemy[3]))
                if self.item:
                    Color(*COLOR_ITEM)
                    Rectangle(pos=(gx + self.item[0], gy + self.item[1]), size=(self.item[2], self.item[3]))
                if self.journal:
                    Color(*COLOR_JOURNAL)
                    Rectangle(pos=(gx + self.journal[0], gy + self.journal[1]), size=(self.journal[2], self.journal[3]))
                if self.lever:
                    Color(*COLOR_LEVER)
                    Rectangle(pos=(gx + self.lever[0], gy + self.lever[1]), size=(self.lever[2], self.lever[3]))
                if self.archive:
                    Color(*COLOR_ARCHIVE)
                    Rectangle(pos=(gx + self.archive[0], gy + self.archive[1]), size=(self.archive[2], self.archive[3]))
                if self.survivor:
                    Color(*COLOR_SURVIVOR)
                    Rectangle(pos=(gx + self.survivor[0], gy + self.survivor[1]), size=(self.survivor[2], self.survivor[3]))
                if self.lever_puzzle:
                    for i, r in enumerate(self.lever_puzzle):
                        if i != self.correct_lever:
                            Color(*COLOR_LEVER_PUZZLE_WRONG)
                        else:
                            Color(*COLOR_LEVER_PUZZLE_CORRECT)
                        Rectangle(pos=(gx + r[0], gy + r[1]), size=(r[2], r[3]))
            else:
                Color(*COLOR_DARKNESS)
                Rectangle(pos=(gx, gy), size=(self.WIDTH, self.HEIGHT))
                # Faint maze visibility in the dark
                Color(0.08, 0.08, 0.08, 1)
                for y in range(self.rows):
                    for x in range(self.cols):
                        if self.maze[y][x] == 1:
                            Rectangle(pos=(gx + x*TILE_SIZE, gy + y*TILE_SIZE), size=(TILE_SIZE, TILE_SIZE))
                # Flashlight around player
                Color(0.30, 0.30, 0.30, 1)
                r = 80
                cx = gx + self.player[0] + self.player[2] / 2
                cy = gy + self.player[1] + self.player[3] / 2
                Ellipse(pos=(cx - r, cy - r), size=(2*r, 2*r))
            Color(*COLOR_PLAYER)
            Rectangle(pos=(gx + self.player[0], gy + self.player[1]), size=(self.player[2], self.player[3]))

    def handle_overlay_action(self, mode, idx, text):
        if mode in ("story", "journal"):
            was_caught = "caught by the shadow" in self.ui.overlay_text
            self.dispatch('on_hide_overlay')
            if was_caught:
                if self.lives != -1:
                    self.lives = max(0, self.lives - 1)
                if self.lives == 0:
                    self.dispatch('on_show_overlay', "gameover", "Game Over", ["OK"])
                else:
                    self.reset_level()
            return
        if mode == "gameover":
            self.dispatch('on_hide_overlay')
            self.ui.manager.transition = NoTransition()
            self.ui.manager.current = 'menu'
            return
        if mode == "riddle":
            ans = (text or "").strip().lower()
            if ans in ("guilt", "shadow"):
                self.dispatch('on_hide_overlay')
                self.level += 1
                self.reset_level()
            return
        if mode == "l4_choice":
            if idx == 1:
                self.l4_mode = "safe"
                self.enemy_speed *= LEVEL_4_SAFE_SPEED_MULTIPLIER
            else:
                self.l4_mode = "fast"
                self.enemy_speed *= LEVEL_4_FAST_SPEED_MULTIPLIER
            self.dispatch('on_hide_overlay')
            return
        if mode == "survivor":
            if idx == 1:
                self.survivor_heeded = True
            else:
                self.survivor_heeded = False
            self.dispatch('on_hide_overlay')
            return
        if mode == "endings":
            self.dispatch('on_hide_overlay')
            self.ui.manager.transition = NoTransition()
            self.ui.manager.current = 'menu'
            return

