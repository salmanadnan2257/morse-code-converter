"""
Tkinter GUI for the Morse code converter.

Wraps the pure functions in morse_converter.py (text_to_morse and
morse_to_text) in a two-way, live-updating desktop interface: type in one
box, see the conversion appear in the other as you type, no submit button
needed. A visual playback panel flashes each dot and dash of the current
Morse sequence in sequence, giving a sense of how the code would sound if
tapped out.

Run with:
    python3 gui.py
"""

import tkinter as tk
from tkinter import ttk

from morse_converter import morse_to_text, text_to_morse

BG = "#1e1e2e"
PANEL_BG = "#282a3a"
FG = "#e8e8f0"
MUTED_FG = "#9a9ab0"
ACCENT = "#7aa2f7"
ERROR_FG = "#f7768e"
DOT_ON = "#7aa2f7"
DASH_ON = "#f7768e"
SYMBOL_OFF = "#44475a"

PLAYBACK_DOT_MS = 220
PLAYBACK_DASH_MS = 420
PLAYBACK_GAP_MS = 160


class MorseApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Morse Code Converter")
        self.root.configure(bg=BG)
        self.root.geometry("760x560")
        self.root.minsize(620, 480)

        self._playback_job = None

        self._build_style()
        self._build_layout()

    # -- styling -----------------------------------------------------
    def _build_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=PANEL_BG,
            foreground=MUTED_FG,
            padding=(18, 10),
            font=("DejaVu Sans", 11),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", ACCENT)],
            foreground=[("selected", "#101018")],
        )
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL_BG)
        style.configure(
            "TButton",
            background=ACCENT,
            foreground="#101018",
            font=("DejaVu Sans", 10, "bold"),
            padding=(10, 6),
            borderwidth=0,
        )
        style.map("TButton", background=[("active", "#5f87e0")])
        style.configure(
            "TLabel", background=BG, foreground=FG, font=("DejaVu Sans", 10)
        )
        style.configure(
            "Muted.TLabel", background=BG, foreground=MUTED_FG, font=("DejaVu Sans", 9)
        )
        style.configure(
            "Error.TLabel", background=BG, foreground=ERROR_FG, font=("DejaVu Sans", 9)
        )

    # -- layout --------------------------------------------------------
    def _build_layout(self) -> None:
        title = tk.Label(
            self.root,
            text="Morse Code Converter",
            bg=BG,
            fg=FG,
            font=("DejaVu Sans", 18, "bold"),
        )
        title.pack(pady=(16, 4))

        subtitle = ttk.Label(
            self.root,
            text="Type in either direction. The result updates as you go.",
            style="Muted.TLabel",
        )
        subtitle.pack(pady=(0, 12))

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        self.text_to_morse_tab = self._build_conversion_tab(
            notebook,
            input_label="Text",
            output_label="Morse code",
            convert_fn=self._safe_text_to_morse,
            playback_source="output",
        )
        self.morse_to_text_tab = self._build_conversion_tab(
            notebook,
            input_label="Morse code (letters space-separated, / between words)",
            output_label="Text",
            convert_fn=self._safe_morse_to_text,
            playback_source="input",
        )

        notebook.add(self.text_to_morse_tab["frame"], text="Text to Morse")
        notebook.add(self.morse_to_text_tab["frame"], text="Morse to Text")

        # Playback panel shared across both tabs.
        playback_frame = ttk.Frame(self.root, style="Panel.TFrame")
        playback_frame.pack(fill="x", padx=16, pady=(4, 16))

        playback_header = tk.Frame(playback_frame, bg=PANEL_BG)
        playback_header.pack(fill="x", padx=12, pady=(10, 4))

        tk.Label(
            playback_header,
            text="Playback",
            bg=PANEL_BG,
            fg=FG,
            font=("DejaVu Sans", 11, "bold"),
        ).pack(side="left")

        self.play_button = ttk.Button(
            playback_header, text="Play", command=self._start_playback
        )
        self.play_button.pack(side="right")

        self.playback_canvas = tk.Canvas(
            playback_frame, height=70, bg=PANEL_BG, highlightthickness=0
        )
        self.playback_canvas.pack(fill="x", padx=12, pady=(0, 12))
        self._symbol_ids = []

    def _build_conversion_tab(
        self, notebook, input_label, output_label, convert_fn, playback_source
    ):
        frame = ttk.Frame(notebook)

        ttk.Label(frame, text=input_label).pack(
            anchor="w", padx=16, pady=(14, 2)
        )
        input_box = tk.Text(
            frame,
            height=6,
            wrap="word",
            bg=PANEL_BG,
            fg=FG,
            insertbackground=FG,
            font=("DejaVu Sans Mono", 11),
            relief="flat",
            padx=10,
            pady=8,
        )
        input_box.pack(fill="x", padx=16)

        error_label = ttk.Label(frame, text="", style="Error.TLabel")
        error_label.pack(anchor="w", padx=16, pady=(4, 0))

        ttk.Label(frame, text=output_label).pack(
            anchor="w", padx=16, pady=(12, 2)
        )
        output_box = tk.Text(
            frame,
            height=6,
            wrap="word",
            bg=PANEL_BG,
            fg=ACCENT,
            insertbackground=FG,
            font=("DejaVu Sans Mono", 11),
            relief="flat",
            padx=10,
            pady=8,
            state="disabled",
        )
        output_box.pack(fill="x", padx=16)

        button_row = ttk.Frame(frame)
        button_row.pack(fill="x", padx=16, pady=10)
        copy_button = ttk.Button(
            button_row,
            text="Copy result",
            command=lambda: self._copy_to_clipboard(output_box),
        )
        copy_button.pack(side="left")

        clear_button = ttk.Button(
            button_row,
            text="Clear",
            command=lambda: self._clear(input_box, output_box, error_label),
        )
        clear_button.pack(side="left", padx=(8, 0))

        tab_state = {
            "frame": frame,
            "input_box": input_box,
            "output_box": output_box,
            "error_label": error_label,
            "convert_fn": convert_fn,
            "playback_source": playback_source,
        }

        input_box.bind(
            "<KeyRelease>", lambda event, s=tab_state: self._on_key_release(s)
        )

        return tab_state

    # -- conversion helpers ---------------------------------------------
    def _safe_text_to_morse(self, raw: str) -> str:
        return text_to_morse(raw)

    def _safe_morse_to_text(self, raw: str) -> str:
        return morse_to_text(raw)

    def _on_key_release(self, tab_state: dict) -> None:
        raw = tab_state["input_box"].get("1.0", "end-1c")
        output_box = tab_state["output_box"]
        error_label = tab_state["error_label"]

        output_box.configure(state="normal")
        if raw.strip() == "":
            output_box.delete("1.0", "end")
            output_box.configure(state="disabled")
            error_label.configure(text="")
            return

        try:
            result = tab_state["convert_fn"](raw)
            error_label.configure(text="")
        except ValueError as exc:
            result = ""
            error_label.configure(text=str(exc))

        output_box.delete("1.0", "end")
        output_box.insert("1.0", result)
        output_box.configure(state="disabled")

    def _copy_to_clipboard(self, output_box: tk.Text) -> None:
        content = output_box.get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(content)

    def _clear(self, input_box, output_box, error_label) -> None:
        input_box.delete("1.0", "end")
        output_box.configure(state="normal")
        output_box.delete("1.0", "end")
        output_box.configure(state="disabled")
        error_label.configure(text="")

    # -- playback --------------------------------------------------------
    def _current_tab_state(self):
        # Whichever tab currently has its output populated with a Morse
        # string drives playback: the Text-to-Morse tab's output, or the
        # Morse-to-Text tab's own input (already Morse).
        for state in (self.text_to_morse_tab, self.morse_to_text_tab):
            box = (
                state["output_box"]
                if state["playback_source"] == "output"
                else state["input_box"]
            )
            content = box.get("1.0", "end-1c").strip()
            if content:
                return content
        return ""

    def _start_playback(self) -> None:
        if self._playback_job is not None:
            self.root.after_cancel(self._playback_job)
            self._playback_job = None

        morse = self._current_tab_state()
        self.playback_canvas.delete("all")
        if not morse:
            return

        symbols = [c for c in morse if c in ".-"]
        self._render_symbols(symbols)
        self._play_index = 0
        self._playback_symbols = symbols
        self._advance_playback()

    def _render_symbols(self, symbols) -> None:
        self.playback_canvas.delete("all")
        x = 12
        y = 35
        self._symbol_boxes = []
        for symbol in symbols:
            width = 14 if symbol == "." else 34
            box = self.playback_canvas.create_oval(
                x, y - 8, x + width, y + 8, fill=SYMBOL_OFF, outline=""
            ) if symbol == "." else self.playback_canvas.create_rectangle(
                x, y - 8, x + width, y + 8, fill=SYMBOL_OFF, outline=""
            )
            self._symbol_boxes.append((box, symbol))
            x += width + 10

    def _advance_playback(self) -> None:
        if self._play_index >= len(self._playback_symbols):
            self._playback_job = None
            return

        box, symbol = self._symbol_boxes[self._play_index]
        color = DOT_ON if symbol == "." else DASH_ON
        duration = PLAYBACK_DOT_MS if symbol == "." else PLAYBACK_DASH_MS
        self.playback_canvas.itemconfigure(box, fill=color)

        def turn_off():
            self.playback_canvas.itemconfigure(box, fill=SYMBOL_OFF)
            self._play_index += 1
            self._playback_job = self.root.after(PLAYBACK_GAP_MS, self._advance_playback)

        self._playback_job = self.root.after(duration, turn_off)


def main() -> None:
    root = tk.Tk()
    MorseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
