"""
Real audio for Morse code playback: tone generation and cross-platform
playback backend detection, standard library only.

Tones are generated as raw 16-bit PCM sine waves and written to WAV files
with the stdlib `wave` module, no third-party audio library involved.
Playback tries, in order: `winsound` (Windows only), then whatever system
command-line player is actually present on the machine (`aplay`, `paplay`,
`afplay`, `ffplay`, checked with `shutil.which` at runtime rather than
assumed). If none of those exist, no audio path is available at all and the
caller is expected to fall back to a visual-only representation instead of
crashing or silently doing nothing.

Timing follows the standard Morse convention, expressed in "units":
    dot                    = 1 unit
    dash                   = 3 units
    gap within a letter    = 1 unit  (between symbols of the same letter)
    gap between letters    = 3 units
    gap between words      = 7 units
"""

import atexit
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import wave

SAMPLE_RATE = 44100
TONE_FREQUENCY_HZ = 700
VOLUME = 0.5

UNIT_MS = 80

DOT_UNITS = 1
DASH_UNITS = 3
INTRA_SYMBOL_GAP_UNITS = 1
INTER_LETTER_GAP_UNITS = 3
INTER_WORD_GAP_UNITS = 7

_PLAYERS_IN_PRIORITY_ORDER = ("aplay", "paplay", "afplay", "ffplay")


def build_timing_sequence(morse: str):
    """Break a Morse string (as produced by text_to_morse) into a sequence
    of ("dot" | "dash" | "gap", units) events with correct standard timing.

    Expects the same format text_to_morse produces and morse_to_text
    consumes: letters space-separated, words separated by " / ".
    """
    events = []
    words = [w for w in morse.strip().split(" / ") if w != ""]
    for w_index, word in enumerate(words):
        letters = [letter for letter in word.split(" ") if letter != ""]
        for l_index, letter in enumerate(letters):
            symbols = [c for c in letter if c in ".-"]
            for s_index, symbol in enumerate(symbols):
                kind = "dot" if symbol == "." else "dash"
                units = DOT_UNITS if symbol == "." else DASH_UNITS
                events.append((kind, units))
                if s_index < len(symbols) - 1:
                    events.append(("gap", INTRA_SYMBOL_GAP_UNITS))
            if l_index < len(letters) - 1:
                events.append(("gap", INTER_LETTER_GAP_UNITS))
        if w_index < len(words) - 1:
            events.append(("gap", INTER_WORD_GAP_UNITS))
    return events


def _sine_pcm_frames(duration_ms, frequency=TONE_FREQUENCY_HZ,
                      sample_rate=SAMPLE_RATE, volume=VOLUME):
    """Raw 16-bit little-endian PCM bytes for a pure sine tone."""
    n_samples = int(sample_rate * duration_ms / 1000)
    amplitude = int(volume * 32767)
    samples = [
        int(amplitude * math.sin(2 * math.pi * frequency * (i / sample_rate)))
        for i in range(n_samples)
    ]
    return struct.pack("<%dh" % len(samples), *samples)


def _silence_pcm_frames(duration_ms, sample_rate=SAMPLE_RATE):
    n_samples = int(sample_rate * duration_ms / 1000)
    return b"\x00\x00" * n_samples


def write_tone_wav(path, duration_ms, frequency=TONE_FREQUENCY_HZ,
                    sample_rate=SAMPLE_RATE):
    """Write a single sine-wave tone of the given duration to a WAV file."""
    frames = _sine_pcm_frames(duration_ms, frequency, sample_rate)
    with wave.open(path, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frames)


def render_morse_to_wav(morse, path, unit_ms=UNIT_MS,
                         frequency=TONE_FREQUENCY_HZ, sample_rate=SAMPLE_RATE):
    """Render an entire Morse string to one WAV file (tone for dots/dashes,
    silence for gaps), used for offline rendering and for verifying that
    playback timing matches the standard Morse ratios."""
    events = build_timing_sequence(morse)
    frames = bytearray()
    for kind, units in events:
        duration_ms = units * unit_ms
        if kind == "gap":
            frames.extend(_silence_pcm_frames(duration_ms, sample_rate))
        else:
            frames.extend(_sine_pcm_frames(duration_ms, frequency, sample_rate))
    with wave.open(path, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(bytes(frames))
    return events


_tmp_dir = None


def _tone_dir():
    global _tmp_dir
    if _tmp_dir is None:
        _tmp_dir = tempfile.mkdtemp(prefix="morse_tones_")
        atexit.register(shutil.rmtree, _tmp_dir, ignore_errors=True)
    return _tmp_dir


def build_symbol_tones(unit_ms=UNIT_MS):
    """Generate a dot-tone WAV and a dash-tone WAV in a temp dir, return
    their paths. Reused for every symbol played rather than regenerated."""
    tone_dir = _tone_dir()
    dot_path = os.path.join(tone_dir, "dot.wav")
    dash_path = os.path.join(tone_dir, "dash.wav")
    write_tone_wav(dot_path, DOT_UNITS * unit_ms)
    write_tone_wav(dash_path, DASH_UNITS * unit_ms)
    return dot_path, dash_path


def detect_playback_backend():
    """Return the name of the audio backend that will actually be used
    ("winsound" or a system player's command name), or None if nothing
    usable was found on this machine. Checked at runtime, nothing assumed.
    """
    if sys.platform == "win32":
        try:
            import winsound  # noqa: F401
            return "winsound"
        except ImportError:
            pass
    for player in _PLAYERS_IN_PRIORITY_ORDER:
        if shutil.which(player):
            return player
    return None


def play_wav_async(path, backend):
    """Fire-and-forget playback of a WAV file through the given backend.
    Non-blocking so the caller (a GUI event loop) can keep the visual
    playback in sync without waiting on the audio process."""
    if backend == "winsound":
        import winsound
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        return None
    if backend == "aplay":
        command = ["aplay", "-q", path]
    elif backend == "paplay":
        command = ["paplay", path]
    elif backend == "afplay":
        command = ["afplay", path]
    elif backend == "ffplay":
        command = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path]
    else:
        raise ValueError(f"Unknown playback backend: {backend!r}")
    return subprocess.Popen(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


if __name__ == "__main__":
    # Quick manual smoke test: render "SOS" and report the backend found.
    from morse_converter import text_to_morse

    morse = text_to_morse("SOS")
    backend = detect_playback_backend()
    print(f"Morse: {morse}")
    print(f"Detected playback backend: {backend!r}")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        events = render_morse_to_wav(morse, tmp.name)
    total_ms = sum(units for _, units in events) * UNIT_MS
    print(f"Rendered {tmp.name}, expected duration ~{total_ms} ms")
