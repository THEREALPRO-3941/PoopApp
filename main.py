"""
PoopApp - runnable Kivy application
Features:
- Start / Stop "Poop Mode"
- Terminal-style typed banner inside a ScrollView (auto-scrolls)
- Sound playback (tries mp3, then wav). Safe if missing.
- Toggle buttons for simple features
- Floating emoji spawn animation when enabled
- Clean shutdown: cancels scheduled events and stops sound
"""
import os
import random
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton
from kivy.animation import Animation

KV = r"""
<MonospaceLabel@Label>:
    font_name: 'RobotoMono' if 'RobotoMono' in Label.get_property_observers('font_name') else None
    text_size: self.width, None
    size_hint_y: None
    markup: True
    valign: 'top'

<PoopRoot>:
    orientation: 'vertical'
    padding: dp(12)
    spacing: dp(10)

    BoxLayout:
        size_hint_y: None
        height: dp(48)
        canvas.before:
            Color:
                rgba: 0, 0, 0, 0.8
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: "[b]💩 Poop Control Panel 💩[/b]"
            markup: True
            color: 0, 1, 0, 1
            font_size: '18sp'

    BoxLayout:
        size_hint_y: None
        height: dp(120)
        spacing: dp(10)
        Label:
            text: "💩"
            font_size: '70sp'
            halign: 'center'
            valign: 'middle'

        BoxLayout:
            orientation: 'vertical'
            spacing: dp(8)
            Button:
                id: start_btn
                text: root.start_button_text
                background_color: (0.1, 0.7, 0.1, 1) if not root.is_running else (0.7,0.2,0.2,1)
                color: (0,0,0,1)
                on_press: root.toggle_poop_mode()

            BoxLayout:
                size_hint_y: None
                height: dp(36)
                spacing: dp(8)
                ToggleButton:
                    id: giggle_toggle
                    text: "Activate Giggle: OFF"
                    state: 'normal'
                    on_state:
                        root.giggle = self.state == 'down'
                        self.text = "Activate Giggle: ON" if self.state == 'down' else "Activate Giggle: OFF"
                ToggleButton:
                    id: spawn_toggle
                    text: "Spawn Emoji: OFF"
                    state: 'normal'
                    on_state:
                        root.spawn_emojis = self.state == 'down'
                        self.text = "Spawn Emoji: ON" if self.state == 'down' else "Spawn Emoji: OFF"

    # Terminal area with ScrollView
    ScrollView:
        id: scroll
        do_scroll_x: False
        bar_width: dp(6)
        effect_cls: 'ScrollEffect'
        MonospaceLabel:
            id: terminal
            size_hint_y: None
            text: root.terminal_text
            font_size: '12sp'
            color: 0, 1, 0, 1

    FloatLayout:
        id: emoji_layer
        size_hint_y: None
        height: dp(120)

    BoxLayout:
        size_hint_y: None
        height: dp(44)
        spacing: dp(8)
        Button:
            text: "Exit"
            background_color: (0.9,0.1,0.1,1)
            on_press: app.stop()
        Button:
            text: "Clear Terminal"
            on_press: root.clear_terminal()
"""

BANNER = """██████╗ ██████╗ ██████╗ ██████╗
██╔══██╗██╔═══██╗██╔═══██╗██╔══██╗
██████╔╝██║   ██║██║   ██║██████╔╝
██╔═══╝ ██║   ██║██║   ██║██╔═══╝ 
██║     ╚██████╔╝╚██████╔╝██║     
╚═╝      ╚═════╝  ╚═════╝ ╚═╝     

💩💩💩💩💩💩💩💩💩💩💩
🚽 P O O P   M O D E 🚽
😂 Congratulations! You have successfully entered...
💩 THE POOP ZONE 💩
No files were harmed. No data was collected. Just poop. 😆😂
💩💩💩💩💩💩💩💩
"""

class PoopRoot(BoxLayout):
    terminal_text = StringProperty("")
    is_running = BooleanProperty(False)
    giggle = BooleanProperty(False)
    spawn_emojis = BooleanProperty(False)
    start_button_text = StringProperty("START POOP MODE")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._typewriter_ev = None
        self._emoji_ev = None
        self._sound = None
        self._banner_idx = 0
        self._load_sound()

    def _load_sound(self):
        """Attempts to load sound files safely from local folder."""
        for ext in ["mp3", "wav"]:
            path = Path(f"sound.{ext}")
            if path.exists():
                self._sound = SoundLoader.load(str(path))
                if self._sound:
                    self._sound.loop = True
                    break

    def toggle_poop_mode(self):
        """Starts or stops the main active loop."""
        if not self.is_running:
            self.start_poop_mode()
        else:
            self.stop_poop_mode()

    def start_poop_mode(self):
        self.is_running = True
        self.start_button_text = "STOP POOP MODE"
        self._banner_idx = 0
        self.terminal_text = ""
        
        # Start typing effect
        self._typewriter_ev = Clock.schedule_interval(self._type_next_char, 0.015)
        
        # Start floating emoji spawner
        self._emoji_ev = Clock.schedule_interval(self._spawn_floating_emoji, 0.4)

        if self._sound:
            self._sound.play()

    def stop_poop_mode(self):
        self.is_running = False
        self.start_button_text = "START POOP MODE"
        
        if self._typewriter_ev:
            self._typewriter_ev.cancel()
        if self._emoji_ev:
            self._emoji_ev.cancel()
            
        if self._sound:
            self._sound.stop()
            
        self.append_terminal("\n[!] Poop mode deactivated.\n")

    def _type_next_char(self, dt):
        """Types out the banner character by character."""
        if self._banner_idx < len(BANNER):
            self.terminal_text += BANNER[self._banner_idx]
            self._banner_idx += 1
            self._auto_scroll()
        else:
            if self._typewriter_ev:
                self._typewriter_ev.cancel()

    def _spawn_floating_emoji(self, dt):
        """Creates floating emoji animations inside the emoji_layer layout."""
        if not self.spawn_emojis or not self.is_running:
            return

        layer = self.ids.emoji_layer
        emojis = ["💩", "🚽", "😂", "💥", "🟢"]
        
        lbl = Label(
            text=random.choice(emojis),
            font_size='24sp',
            size_hint=(None, None),
            size=(dp(30), dp(30)),
            pos=(random.randint(0, int(layer.width - dp(30))), 0)
        )
        layer.add_widget(lbl)

        # Animate upward + fade out
        anim = Animation(
            y=layer.height - dp(30),
            opacity=0,
            duration=random.uniform(1.2, 2.5)
        )
        anim.bind(on_complete=lambda a, w: layer.remove_widget(w))
        anim.start(lbl)

        if self.giggle and random.random() > 0.6:
            self.append_terminal("😂 *gasp/giggle*\n")

    def append_terminal(self, text):
        self.terminal_text += text
        self._auto_scroll()

    def _auto_scroll(self):
        """Forces the terminal scrollview to stay at the bottom."""
        def scroll_to_bottom(dt):
            self.ids.terminal.height = self.ids.terminal.texture_size[1]
            self.ids.scroll.scroll_y = 0
        Clock.schedule_once(scroll_to_bottom, 0)

    def clear_terminal(self):
        self.terminal_text = ""


class PoopApp(App):
    def build(self):
        Builder.load_string(KV)
        return PoopRoot()

    def on_stop(self):
        # Ensures safe exit and cleans up background sounds/clocks
        if hasattr(self, 'root') and self.root:
            self.root.stop_poop_mode()


if __name__ == "__main__":
    PoopApp().run()
