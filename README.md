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
- A "Play" button that visually flashes each dot and dash of the current
  Morse sequence in order, dots as short pulses, dashes as longer ones, so
  you can see the rhythm of a message without needing audio.
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

There is no persistence, no network calls, no configuration.

## Setup

Requires Python 3 with a Tk-enabled install (`tkinter` ships with the
standard CPython installer on Windows and macOS; on Linux it may need a
separate OS package, e.g. `python3-tk` on Debian/Ubuntu). No third-party
packages, no environment variables, no `.env` file needed.

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
clipboard. The "Play" button below the tabs flashes the dots and dashes of
whatever Morse is currently on screen, one symbol at a time.

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
- Considered playing real audio beeps for the dot/dash playback (a sine
  wave through the stdlib `wave`/`audioop` modules or a small library like
  `simpleaudio`), but `winsound` is Windows-only and there is no
  cross-platform, dependency-free way to play a tone from the standard
  library alone. Went with a purely visual playback instead: a canvas that
  flashes each dot and dash in sequence, with dashes held on screen longer
  than dots, matching the actual duration convention. It needs nothing
  beyond tkinter and works identically on any platform.
- Binding conversion to `<KeyRelease>` on a multi-line `Text` widget means
  the conversion function reruns on every keystroke, including invalid
  intermediate states (e.g. typing a partial word). Caught `ValueError` at
  the GUI layer and show it as a small inline message instead of leaving
  the output box stale or crashing the app mid-keystroke.

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
- The playback feature is visual only, no audible tone. If picking this up
  again with more time budget for dependencies, a small optional audio
  backend (falling back gracefully when no audio device is present) would
  make the playback genuinely represent what Morse code sounds like, not
  just its timing pattern.
