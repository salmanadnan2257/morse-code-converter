# Morse Code Converter

A desktop GUI that converts text to International Morse Code and decodes
Morse code back into text, live, as you type.

## Why it exists

Practice exercise for working with dictionary lookups and basic string
processing in Python, extended into a small tkinter application to practice
building an actual interface around that logic instead of a bare
input/print loop.

## Features

- Two-way conversion: a "Text to Morse" tab and a "Morse to Text" tab, both
  updating live on every keystroke, no submit button.
- Converts letters (A-Z), digits (0-9), and common punctuation in either
  direction.
- Case-insensitive input on the text side.
- Words are separated with a `/` in Morse output, the conventional Morse
  word separator, and `morse_to_text()` expects the same convention on the
  way back in.
- Raises a clear error if a character or Morse symbol has no mapping,
  instead of crashing with a raw `KeyError`; the GUI surfaces this as an
  inline message rather than a stack trace.
- A "Play" button that plays the current Morse sequence as real audio
  beeps (a 700 Hz sine tone) while visually flashing each dot and dash in
  sync on a canvas, dots as short pulses, dashes as longer ones. Timing
  follows the standard Morse ratios exactly: dot = 1 unit, dash = 3 units,
  gap within a letter = 1 unit, gap between letters = 3 units, gap between
  words = 7 units (1 unit = 80 ms here).
- Audio backend is detected at startup, not assumed: it tries a system
  command-line player (`aplay`, `paplay`, `afplay`, `ffplay`, checked with
  `shutil.which`) and, on Windows, the stdlib `winsound` module. If none of
  those exist on the machine, the app says so plainly in the playback panel
  ("No audio output available on this system, showing visual playback
  only") and keeps the visual flash working on its own rather than
  crashing or failing silently.
- "Copy result" button that puts the converted text on the system clipboard
  using tkinter's built-in `clipboard_append`, no extra dependency.

## Architecture

`morse_converter.py` holds all the conversion logic and no UI code:
`MORSE_CODE` maps each supported character to its Morse pattern, `TEXT_CODE`
is the same dictionary inverted, `text_to_morse()` uppercases input and
looks up each character, and `morse_to_text()` splits Morse input on `/` for
words and whitespace for letters and looks each symbol up in `TEXT_CODE`.
Both raise `ValueError` naming the offending character or symbol instead of
letting a bare `KeyError` escape. Running the file directly still gives the
original one-line CLI prompt.

`gui.py` is a separate tkinter front end that imports those two functions
and does nothing else with the conversion logic; it just wires text
widgets to them on `<KeyRelease>`, manages the two-tab layout, the
clipboard button, and the dot/dash playback canvas. Keeping the logic and
the UI in separate files means the conversion functions can be tested
directly with no tkinter dependency, which is what the test commands below
do.

`morse_audio.py` holds everything audio-related, also with no tkinter
dependency: `build_timing_sequence()` turns a Morse string into an ordered
list of `("dot" | "dash" | "gap", units)` events using the standard timing
ratios; `write_tone_wav()` builds a mono 16-bit PCM sine wave with the
stdlib `wave` module and writes it straight to a WAV file, no third-party
audio library involved; `build_symbol_tones()` renders one dot-tone WAV and
one dash-tone WAV once per app run and reuses them for every symbol played;
`detect_playback_backend()` checks, at runtime, what's actually installed
(`winsound` on Windows, otherwise `shutil.which` against `aplay`, `paplay`,
`afplay`, `ffplay` in that order) and returns the first match or `None`;
`play_wav_async()` fires off playback through whichever backend was found
as a non-blocking `subprocess.Popen` call (or `winsound.PlaySound` with
`SND_ASYNC`), so the GUI's visual flashing and the audio never block each
other. `gui.py` calls `build_timing_sequence()` to drive both the canvas
flash and the tone playback from the exact same event list, so what you see
and what you hear are always the same timeline, not two independently
approximated ones. `render_morse_to_wav()` renders a whole message,
silence and all, to a single WAV file; it exists for offline rendering and
was how the timing was verified against expected duration during
development (see Challenges).

There is no persistence, no network calls, no configuration.

## Setup

Requires Python 3 with a Tk-enabled install (`tkinter` ships with the
standard CPython installer on Windows and macOS; on Linux it may need a
separate OS package, e.g. `python3-tk` on Debian/Ubuntu). No third-party
packages, no environment variables, no `.env` file needed. Audio playback
also needs nothing extra to install for generation (the `wave` module is
stdlib), but actually hearing a tone depends on whatever the host OS
already has: `aplay` or `paplay` on Linux, `afplay` on macOS (built in),
`winsound` on Windows (built in), or `ffplay` if FFmpeg happens to be
installed. In the Linux container this project was built and verified in,
both `aplay` and `ffplay` were present; `detect_playback_backend()` picks
`aplay` first since it's earlier in the priority order, and that is the
backend actually exercised end to end (WAV rendered, played through
`aplay`, exit code checked). If a machine has none of these, the app still
runs fine, just visually, and says so in the playback panel.

```bash
cd morse-code-converter
python3 gui.py
```

## Usage

Launch the GUI, pick a tab, and start typing:

- "Text to Morse": type a message in the top box, the Morse code appears in
  the bottom box as you type.
- "Morse to Text": type or paste Morse code (letters space-separated, `/`
  between words) in the top box, the decoded text appears below.

Either tab's "Copy result" button copies the current output to the
clipboard. The "Play" button below the tabs plays the dots and dashes of
whatever Morse is currently on screen as real tones, one symbol at a time,
while flashing the same sequence on the canvas in sync. A status line under
the canvas names the audio backend actually in use (e.g. "Audio backend:
aplay"), or states plainly that no audio output is available if the
detection found nothing.

The original CLI still works for a quick one-off conversion without opening
a window:

```
$ python3 morse_converter.py
Enter a message to be converted into Morse code: SOS HELLO WORLD
... --- ... / .... . .-.. .-.. --- / .-- --- .-. .-.. -..
```

That is a real run of the script in this folder.

## Challenges

- The source script this was built from was missing a mapping for the letter
  `V`, so any input containing V would crash with a `KeyError`. Added
  `"V": "...-"` to the table.
- The original used a 7-dot string (`"......."`) to represent a space between
  words, which is not standard Morse notation and reads oddly in output.
  Switched to `/`, the conventional word separator used in ITU Morse
  transcription, and confirmed it still round-trips visually against the
  reference alphabet.
- Looking up an unmapped character used to throw a bare `KeyError` from deep
  inside the dictionary. Wrapped the lookup so unsupported characters raise a
  `ValueError` naming the offending character.
- Adding `morse_to_text()` needed a word separator that survives a round
  trip. Because `text_to_morse()` joins per-character codes with a single
  space and the space character itself maps to `/`, every word boundary in
  the output is literally the three characters `" / "`. Splitting on that
  exact string decodes cleanly; splitting naively on `/` alone would have
  left stray spaces around each word.
- Originally shipped playback as visual-only because `winsound` is
  Windows-only and there seemed to be no dependency-free way to make a
  sound from the standard library alone. That was wrong: `wave` can write
  a real sine-wave WAV file with nothing but stdlib math, and every
  mainstream OS already ships a command-line player capable of playing it
  (`aplay`/`paplay` on Linux, `afplay` on macOS, `winsound` on Windows).
  Rebuilt playback in `morse_audio.py` around that: generate the WAV,
  detect what's actually installed with `shutil.which` at runtime (never
  assumed), and play through the first match. No third-party audio library
  needed after all.
- The original playback loop only knew about individual dot/dash symbols
  and used one flat, approximate gap between all of them (160 ms,
  regardless of whether it was a gap inside a letter, between letters, or
  between words). Standard Morse timing distinguishes those three gaps (1,
  3, and 7 units), and the dot/dash ratio itself was off too (220 ms vs.
  420 ms is roughly 1:1.9, not the correct 1:3). Rewrote the timing as
  `build_timing_sequence()`, which walks the same `" / "`/`" "` structure
  `morse_to_text()` already parses and emits an explicit list of
  `(kind, units)` events, so the audio and the visual flash both read off
  the identical timeline instead of two separately hand-tuned ones.
- Getting the audio and the visual flash to move at exactly the same
  moment mattered more than getting either one "right" in isolation. Using
  `subprocess.Popen` (fire-and-forget, not `.run()`/`.wait()`) to start
  each tone keeps the GUI's `tkinter.after()` timer in charge of the whole
  timeline; if playback had blocked waiting for the audio process to exit,
  the visual flash would lag behind the sound by however long that symbol's
  tone took to finish playing.
- Binding conversion to `<KeyRelease>` on a multi-line `Text` widget means
  the conversion function reruns on every keystroke, including invalid
  intermediate states (e.g. typing a partial word). Caught `ValueError` at
  the GUI layer and show it as a small inline message instead of leaving
  the output box stale or crashing the app mid-keystroke.
- **Diagramming the shared playback source.** The playback panel is one
  canvas shared by two tabs, and `_current_tab_state()` picks which tab's
  Morse content to animate with a fixed priority (Text-to-Morse tab's output
  first, Morse-to-Text tab's input only as a fallback) rather than "whichever
  was typed most recently." A first draft of the architecture diagram implied
  the two tabs fed the canvas symmetrically, which doesn't match the code;
  redrew it as an explicit priority check so the diagram doesn't overstate
  how the source is chosen.
- **Verifying claimed timing against a hand-written formula, not just the
  code's own output.** To confirm the audio was really following standard
  Morse ratios rather than just trusting the implementation, I computed an
  expected duration for a test message by hand from the dot/dash/gap unit
  counts and compared it to the rendered WAV's actual frame count. The two
  matched exactly once the expected-duration calculation used the same
  per-boundary gap rule the code does (1 unit inside a letter, 3 between
  letters, 7 between words); an earlier draft of that check used a single
  flat gap for everything and reported a false mismatch that wasn't a bug in
  the audio code at all, it was a bug in the verification arithmetic.

## What I learned

- A hardcoded lookup table is fine for a fixed, well-known alphabet like
  Morse code; the discipline is in getting the table complete and testing it
  against every character class (letters, digits, punctuation, whitespace).
- Keeping the conversion functions in their own module with no tkinter
  import made them trivial to unit test directly; the GUI became a thin
  consumer of already-correct logic rather than something that needed its
  own conversion tests.
- Small scripts still benefit from being wrapped in functions instead of
  bare module-level code. It's the difference between "a script" and
  "a script with something importable in it," and it costs nothing here.

## What I'd do differently

- No automated unit tests committed to the repo. The round-trip and error
  cases were verified manually (see below); for a dictionary this size,
  a real test file asserting every character class would catch a silently
  wrong table entry that manual spot-checks might miss.
- No handling for characters entirely outside the table's design, like
  accented Latin letters beyond `¿`/`¡`, or Unicode more broadly.
- Audio playback shells out to a system command-line player rather than
  writing samples directly to an audio device, so there's a small,
  unavoidable process-spawn delay on every symbol and no way to know for
  certain a tone finished playing (it's fire-and-forget, matched to the
  visual timer rather than to the subprocess's own lifecycle). A real
  cross-platform audio device API would remove that gap but pulls in a
  third-party dependency this project deliberately avoids.
- Only tested audio playback in this project's own Linux container, with
  `aplay` and `ffplay` both present. `winsound` (Windows) and `afplay`
  (macOS) paths are exercised by the same code but were only verified by
  reading their documented behavior, not by running on those platforms.
