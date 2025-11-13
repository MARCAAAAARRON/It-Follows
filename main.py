from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window

import random

# Basic sizes
TILE = 40

class MenuScreen(Screen):
    pass

class DifficultyScreen(Screen):
    pass

class GameScreen(Screen):
    night_text = StringProperty("Night 1/10")
    light_text = StringProperty("Light: 3")
    time_text = StringProperty("Time: 0")

    # Difficulty settings
    difficulty = StringProperty("normal")
    drain_active = NumericProperty(0.0)
    drain_idle = NumericProperty(0.0)
    enemy_multiplier = NumericProperty(1.0)

    # Overlay state
    overlay_mode = StringProperty("")  # "story", "journal", "riddle", "survivor", "endings"
    overlay_text = StringProperty("")
    overlay_btn1 = StringProperty("")
    overlay_btn2 = StringProperty("")
    overlay_btn3 = StringProperty("")
    overlay_btn4 = StringProperty("")
    riddle_input = StringProperty("")
    overlay_visible = NumericProperty(0)  # 0 hidden, 1 shown

    def on_pre_enter(self):
        self.engine = GameEngine(self)
        self.engine.difficulty = self.difficulty
        # Apply difficulty
        if self.difficulty == "normal":
            self.drain_active = 0.0
            self.drain_idle = 0.0
            self.enemy_multiplier = 1.0
        elif self.difficulty == "hard":
            self.drain_active = 12.0
            self.drain_idle = 1.0
            self.enemy_multiplier = 1.0
        else:  # extreme
            self.drain_active = 12.0
            self.drain_idle = 1.0
            self.enemy_multiplier = 1.35
        self.engine.apply_difficulty(self.drain_active, self.drain_idle, self.enemy_multiplier)
        self.engine.start()

    def on_leave(self):
        self.engine.stop()

    # Touch controls
    def move_left(self):
        self.engine.input_dir[0] = -1
    def move_right(self):
        self.engine.input_dir[0] = 1
    def move_up(self):
        self.engine.input_dir[1] = 1
    def move_down(self):
        self.engine.input_dir[1] = -1
    def stop_h(self):
        self.engine.input_dir[0] = 0
    def stop_v(self):
        self.engine.input_dir[1] = 0
    def use_light(self):
        self.engine.use_light()

    # Overlay controls
    def show_overlay(self, mode, text, btns=None):
        self.overlay_mode = mode
        self.overlay_text = text
        btns = btns or []
        labels = ["", "", "", ""]
        for i, b in enumerate(btns[:4]):
            labels[i] = b
        self.overlay_btn1, self.overlay_btn2, self.overlay_btn3, self.overlay_btn4 = labels
        self.overlay_visible = 1
        if mode == "riddle":
            self.riddle_input = ""

    def hide_overlay(self):
        self.overlay_visible = 0
        self.overlay_mode = ""

    def overlay_action(self, idx):
        if not self.overlay_visible:
            return
        self.engine.handle_overlay_action(self.overlay_mode, idx, self.riddle_input)

class GameEngine:
    WIDTH = Window.width
    HEIGHT = Window.height
    MAX_LEVELS = 10

    def __init__(self, ui: GameScreen):
        self.ui = ui
        self.canvas = ui.ids.gamecanvas
        self.cols = self.WIDTH // TILE
        self.rows = int((self.HEIGHT * 0.75) // TILE)  # leave room for HUD and controls
        self.player = [TILE, TILE, TILE-10, TILE-10]
        self.goal = [self.WIDTH - 2*TILE, int(self.HEIGHT*0.75) - 2*TILE, TILE-10, TILE-10]
        self.enemy = None
        self.item = None
        self.key = None
        self.journal = None
        self.lever = None
        self.archive = None
        self.lever_puzzle = []  # list of rects
        self.correct_lever = -1
        self.survivor = None
        self.level = 1
        self.enemy_speed = 1.6
        self.speed = 5
        self.echo_uses = 3
        self.echo_duration = 3.0
        self.echo_time = -10.0
        self.enemy_active = False
        self.key_collected = False
        self.timer = 0.0
        self.torch_battery = 100.0
        self.drain_active = 0.0
        self.drain_idle = 0.0
        self.enemy_multiplier = 1.0
        self.input_dir = [0, 0]
        self._ev = None
        self.reset_level()

    def apply_difficulty(self, da, di, em):
        self.drain_active = da
        self.drain_idle = di
        self.enemy_multiplier = em
        self.enemy_speed = (1.6 + 0.12 * (self.level - 1)) * self.enemy_multiplier

    def start(self):
        self._ev = Clock.schedule_interval(self.update, 1/60)

    def stop(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None

    def make_rect(self):
        x = random.randint(1, self.cols-2) * TILE
        y = random.randint(1, self.rows-2) * TILE
        return [x, y, TILE-10, TILE-10]

    def generate_maze(self, density=0.25):
        maze = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        for y in range(self.rows):
            for x in range(self.cols):
                if random.random() < density and (x, y) not in [(1, 1), (self.cols-2, self.rows-2)]:
                    maze[y][x] = 1
        return maze

    def reset_level(self):
        self.maze = self.generate_maze(0.25 + 0.02 * (self.level - 1))
        self.player[0], self.player[1] = TILE, TILE
        self.enemy = self.make_rect()
        self.item = self.make_rect()
        self.key = self.make_rect()
        self.journal = None
        self.lever = None
        self.archive = None
        self.lever_puzzle = []
        self.correct_lever = -1
        self.survivor = None
        self.key_collected = False
        self.enemy_active = False
        self.echo_uses = 3
        self.echo_time = -10.0
        self.timer = 0.0
        self.enemy_speed = (1.6 + 0.12 * (self.level - 1)) * self.enemy_multiplier
        self.ui.night_text = f"Night {self.level}/{self.MAX_LEVELS}"
        self.ui.light_text = f"Light: {self.echo_uses}"
        # Narrative placements
        if self.level == 2:
            self.journal = self.make_rect()
        if self.level == 3:
            self.lever = self.make_rect()
        if self.level == 4:
            self.journal = self.make_rect()
        if self.level == 6:
            self.archive = self.make_rect()
        if self.level == 7:
            self.survivor = self.make_rect()
        if self.level == 8:
            # build 10 levers, pick correct
            self.lever_puzzle = [self.make_rect() for _ in range(10)]
            self.correct_lever = random.randint(0, 9)

    def rects_collide(self, a, b):
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        return (ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by)

    def collides_walls(self, r):
        x, y, w, h = r
        for yy in range(self.rows):
            for xx in range(self.cols):
                if self.maze[yy][xx] == 1:
                    rx, ry, rw, rh = xx*TILE, yy*TILE, TILE, TILE
                    if (x < rx + rw and x + w > rx and y < ry + rh and y + h > ry):
                        return True
        return False

    def use_light(self):
        if self.echo_uses > 0:
            self.echo_time = self.timer
            self.echo_uses -= 1
            self.enemy_active = True
            self.ui.light_text = f"Light: {self.echo_uses}"

    def update(self, dt):
        # time and battery
        self.timer += dt
        drain = self.drain_active if (self.timer - self.echo_time) < self.echo_duration else self.drain_idle
        self.torch_battery = max(0.0, self.torch_battery - drain * dt)
        if self.torch_battery <= 0 and (self.timer - self.echo_time) < self.echo_duration:
            self.echo_time = -10.0

        # player move
        move_vec = [self.input_dir[0]*self.speed, -self.input_dir[1]*self.speed]
        new_rect = [self.player[0] + move_vec[0], self.player[1] + move_vec[1], self.player[2], self.player[3]]
        if not self.collides_walls(new_rect):
            self.player = new_rect

        # enemy movement
        echo_active = (self.timer - self.echo_time) < self.echo_duration
        if self.enemy_active and not echo_active:
            ex, ey = self.enemy[0], self.enemy[1]
            px, py = self.player[0], self.player[1]
            dx, dy = px - ex, py - ey
            length = max(1.0, (dx*dx + dy*dy) ** 0.5)
            ex += (dx/length) * self.enemy_speed
            ey += (dy/length) * self.enemy_speed
            self.enemy[0], self.enemy[1] = ex, ey

        # collisions
        if not self.key_collected and self.rects_collide(self.player, self.key):
            self.key_collected = True
        if self.rects_collide(self.player, self.item):
            self.echo_uses += 1
            self.ui.light_text = f"Light: {self.echo_uses}"
            self.item = self.make_rect()
        # Journals
        if self.journal and self.rects_collide(self.player, self.journal):
            self.journal = None
            if self.level == 2:
                self.ui.show_overlay("journal", "Journal: Project Umbra—light reveals, shadow consumes.", ["OK"])
            elif self.level == 4:
                self.ui.show_overlay("journal", "Journal: Subjects report a presence when light fails.", ["OK"])
        # Lever memory L3
        if self.lever and self.rects_collide(self.player, self.lever):
            self.lever = None
            self.ui.show_overlay("story", "Memory: You built this. The maze was your experiment.", ["OK"])
        # Archive L6
        if self.archive and self.rects_collide(self.player, self.archive):
            self.archive = None
            self.ui.show_overlay("story", "Archive: Lead: Eli. Trials escalated. One subject lost.", ["OK"])
        # Survivor L7
        if self.survivor and self.rects_collide(self.player, self.survivor):
            self.survivor = None
            self.ui.show_overlay("survivor", "A survivor begs: 'Don't pull the final lever.'", ["Heed", "Ignore"])
        # Lever puzzle L8
        if self.level == 8 and self.lever_puzzle:
            for i, r in enumerate(list(self.lever_puzzle)):
                if self.rects_collide(self.player, r):
                    if i == self.correct_lever:
                        self.key_collected = True
                        self.ui.show_overlay("story", "The gate hums open.", ["OK"])
                    else:
                        # wrong lever, remove and speed up enemy slightly
                        self.lever_puzzle.pop(i)
                        self.enemy_speed *= 1.12
                        self.ui.show_overlay("story", "Wrong lever. The shadow stirs...", ["OK"])
                    break
        if self.key_collected and self.rects_collide(self.player, self.goal):
            if self.level < self.MAX_LEVELS:
                # Night 5: riddle gate
                if self.level == 5:
                    self.ui.show_overlay("riddle", "Riddle: What follows but never leads?", ["Submit"])            
                else:
                    self.level += 1
                    self.reset_level()
            else:
                # endings
                self.ui.show_overlay("endings", "Act III: Escape or Embrace", ["Escape", "Stay", "Destroy", "Merge"])
                return
        if self.rects_collide(self.player, self.enemy):
            # reset current night on catch
            self.reset_level()

        # draw
        self.draw(echo_active)
        self.ui.time_text = f"Time: {int(self.timer)}"

    def draw(self, echo_active: bool):
        self.canvas.canvas.clear()
        with self.canvas.canvas:
            # background
            Color(0, 0, 0, 1)
            Rectangle(pos=(0, 0), size=(self.WIDTH, self.HEIGHT))
            if echo_active:
                # draw maze
                Color(0.12, 0.12, 0.12, 1)
                for y in range(self.rows):
                    for x in range(self.cols):
                        if self.maze[y][x] == 1:
                            Rectangle(pos=(x*TILE, y*TILE), size=(TILE, TILE))
                # key/goal/enemy/item
                if not self.key_collected:
                    Color(1, 0.6, 0, 1)
                    Rectangle(pos=(self.key[0], self.key[1]), size=(self.key[2], self.key[3]))
                if self.key_collected:
                    Color(0, 1, 0.4, 1)
                    Rectangle(pos=(self.goal[0], self.goal[1]), size=(self.goal[2], self.goal[3]))
                Color(1, 0.2, 0.2, 1)
                Rectangle(pos=(self.enemy[0], self.enemy[1]), size=(self.enemy[2], self.enemy[3]))
                Color(1, 1, 0, 1)
                Rectangle(pos=(self.item[0], self.item[1]), size=(self.item[2], self.item[3]))
                # journals/lever/archive/survivor/levers
                if self.journal:
                    Color(0, 0.8, 0.8, 1)
                    Rectangle(pos=(self.journal[0], self.journal[1]), size=(self.journal[2], self.journal[3]))
                if self.lever:
                    Color(0.6, 0.3, 1, 1)
                    Rectangle(pos=(self.lever[0], self.lever[1]), size=(self.lever[2], self.lever[3]))
                if self.archive:
                    Color(1, 1, 1, 1)
                    Rectangle(pos=(self.archive[0], self.archive[1]), size=(self.archive[2], self.archive[3]))
                if self.survivor:
                    Color(0.7, 0.7, 1, 1)
                    Rectangle(pos=(self.survivor[0], self.survivor[1]), size=(self.survivor[2], self.survivor[3]))
                if self.lever_puzzle:
                    for i, r in enumerate(self.lever_puzzle):
                        Color(0.8, 0.5, 1, 1) if i != self.correct_lever else Color(0.5, 1, 0.8, 1)
                        Rectangle(pos=(r[0], r[1]), size=(r[2], r[3]))
            else:
                # dim world
                Color(0.1, 0.1, 0.1, 1)
                Rectangle(pos=(0, 0), size=(self.WIDTH, self.HEIGHT))
            # player
            Color(0.2, 0.5, 1, 1)
            Rectangle(pos=(self.player[0], self.player[1]), size=(self.player[2], self.player[3]))

    def handle_overlay_action(self, mode, idx, text):
        # idx is 1..4
        if mode in ("story", "journal"):
            self.ui.hide_overlay()
            return
        if mode == "riddle":
            ans = (text or "").strip().lower()
            if ans in ("guilt", "shadow"):
                self.ui.hide_overlay()
                self.level += 1
                self.reset_level()
            # else keep overlay; user can retry
            return
        if mode == "survivor":
            # 1 Heed, 2 Ignore
            self.ui.hide_overlay()
            return
        if mode == "endings":
            # Any ending returns to menu
            self.ui.hide_overlay()
            self.ui.manager.transition = NoTransition()
            self.ui.manager.current = 'menu'
            return

class ItFollowsApp(App):
    def build(self):
        Builder.load_file('itfollows.kv')
        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(DifficultyScreen(name='difficulty'))
        sm.add_widget(GameScreen(name='game'))
        return sm

if __name__ == '__main__':
    ItFollowsApp().run()
