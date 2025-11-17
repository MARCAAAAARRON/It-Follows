from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from engine import GameEngine
from constants import *

class MenuScreen(Screen):
    pass

class DifficultyScreen(Screen):
    pass

class GameScreen(Screen):
    night_text = StringProperty(f"Night 1/{MAX_LEVELS}")
    light_text = StringProperty(f"Light: {INITIAL_ECHO_USES}")
    time_text = StringProperty("Time: 0")
    lives_text = StringProperty("Lives: 3")

    difficulty = StringProperty("normal")
    drain_active = NumericProperty(0.0)
    drain_idle = NumericProperty(0.0)
    enemy_multiplier = NumericProperty(1.0)

    overlay_mode = StringProperty("")
    overlay_text = StringProperty("")
    overlay_btn1 = StringProperty("")
    overlay_btn2 = StringProperty("")
    overlay_btn3 = StringProperty("")
    overlay_btn4 = StringProperty("")
    riddle_input = StringProperty("")
    overlay_visible = NumericProperty(0)

    def on_pre_enter(self):
        self.engine = GameEngine(self)
        self.engine.bind(on_show_overlay=self.show_overlay)
        self.engine.bind(on_hide_overlay=self.hide_overlay)
        self.engine.bind(on_update_ui=self.update_ui)

        # Load and play background horror sound
        try:
            self.bg_sound = SoundLoader.load('itfollows.mp3')
            if self.bg_sound:
                self.bg_sound.loop = True
                self.bg_sound.play()
        except Exception as e:
            print(f"Could not load background sound: {e}")

        if self.difficulty == "freeroam":
            self.drain_active = 0.0
            self.drain_idle = 0.0
            self.enemy_multiplier = 0.0
            self.engine.lives = -1
            self.engine.free_roam = True
            self.engine.echo_uses = 999999
        elif self.difficulty == "easy":
            self.drain_active = NORMAL_DRAIN_ACTIVE
            self.drain_idle = NORMAL_DRAIN_IDLE
            self.enemy_multiplier = NORMAL_ENEMY_MULTIPLIER
            self.engine.lives = -1
        elif self.difficulty == "normal":
            self.drain_active = NORMAL_DRAIN_ACTIVE
            self.drain_idle = NORMAL_DRAIN_IDLE
            self.enemy_multiplier = NORMAL_ENEMY_MULTIPLIER
            self.engine.lives = 3
        elif self.difficulty == "hard":
            self.drain_active = HARD_DRAIN_ACTIVE
            self.drain_idle = HARD_DRAIN_IDLE
            self.enemy_multiplier = HARD_ENEMY_MULTIPLIER
            self.engine.lives = 3
        else:
            self.drain_active = EXTREME_DRAIN_ACTIVE
            self.drain_idle = EXTREME_DRAIN_IDLE
            self.enemy_multiplier = EXTREME_ENEMY_MULTIPLIER
            self.engine.lives = 3

        self.engine.apply_difficulty(self.drain_active, self.drain_idle, self.enemy_multiplier)
        self.engine.start()
        if 'gamecanvas' in self.ids:
            self.on_canvas_size(self.ids.gamecanvas)

    def on_leave(self):
        if hasattr(self, "engine") and self.engine:
            self.engine.stop()
        # Stop background sound
        if hasattr(self, "bg_sound") and self.bg_sound:
            self.bg_sound.stop()

    def move_left(self):
        if hasattr(self, "engine"): self.engine.input_dir[0] = -1
    def move_right(self):
        if hasattr(self, "engine"): self.engine.input_dir[0] = 1
    def move_up(self):
        if hasattr(self, "engine"): self.engine.input_dir[1] = 1
    def move_down(self):
        if hasattr(self, "engine"): self.engine.input_dir[1] = -1
    def stop_h(self):
        if hasattr(self, "engine"): self.engine.input_dir[0] = 0
    def stop_v(self):
        if hasattr(self, "engine"): self.engine.input_dir[1] = 0
    def use_light(self):
        if hasattr(self, "engine"): self.engine.use_light()

    def toggle_music(self):
        """Toggle background music mute/unmute"""
        app = App.get_running_app()
        app.music_muted = not app.music_muted
        if hasattr(self, "bg_sound") and self.bg_sound:
            if app.music_muted:
                self.bg_sound.stop()
            else:
                self.bg_sound.play()

    def show_overlay(self, instance, mode, text, btns=None):
        prev_mode = self.overlay_mode
        self.overlay_mode = mode
        self.overlay_text = text
        btns = btns or []
        labels = ["", "", "", ""]
        for i, b in enumerate(btns[:4]):
            labels[i] = b
        self.overlay_btn1, self.overlay_btn2, self.overlay_btn3, self.overlay_btn4 = labels
        self.overlay_visible = 1
        if mode == "riddle" and prev_mode != "riddle":
            self.riddle_input = ""

    def hide_overlay(self, instance=None):
        self.overlay_visible = 0
        self.overlay_mode = ""

    def update_ui(self, instance, night_text, light_text, time_text, lives_text):
        self.night_text = night_text
        self.light_text = light_text
        self.time_text = time_text
        self.lives_text = lives_text

    def overlay_action(self, idx):
        if not getattr(self, "engine", None):
            return
        if not self.overlay_visible:
            return
        self.engine.handle_overlay_action(self.overlay_mode, idx, self.riddle_input)

    def on_back_button(self):
        """Handle back button press"""
        sm = self.manager
        if sm is None:
            return
        cur = sm.current
        if cur == 'game':
            gs = sm.get_screen('game')
            # If an overlay is visible, close it first
            if getattr(gs, 'overlay_visible', 0):
                gs.hide_overlay()
                return
            sm.transition = NoTransition()
            sm.current = 'menu'
        elif cur == 'difficulty':
            sm.transition = NoTransition()
            sm.current = 'menu'

    def on_canvas_size(self, widget):
        if hasattr(self, "engine") and widget is not None:
            self.engine.set_canvas_size(widget.width, widget.height)

class ItFollowsApp(App):
    music_muted = False
    
    def build(self):
        Builder.load_file('itfollows.kv')
        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(DifficultyScreen(name='difficulty'))
        sm.add_widget(GameScreen(name='game'))
        # Handle Android back/escape
        Window.bind(on_keyboard=self._on_key)
        return sm

    def _on_key(self, window, key, scancode, codepoint, modifier):
        # 27 is Escape / Android Back
        if key == 27:
            sm = self.root
            if sm is None:
                return False
            cur = sm.current
            if cur == 'game':
                gs = sm.get_screen('game')
                # If an overlay is visible, close it first
                if getattr(gs, 'overlay_visible', 0):
                    gs.hide_overlay()
                    return True
                sm.transition = NoTransition()
                sm.current = 'menu'
                return True
            if cur == 'difficulty':
                sm.transition = NoTransition()
                sm.current = 'menu'
                return True
            # On menu, allow default behavior
            return False
        return False

if __name__ == '__main__':
    ItFollowsApp().run()
