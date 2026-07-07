"""
Text to Morse code converter, and back.

Converts a line of text typed by the user into Morse code, and decodes
Morse code back into text, using the standard International Morse Code
alphabet (letters, digits, and common punctuation).
"""

MORSE_CODE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".",
    "F": "..-.", "G": "--.", "H": "....", "I": "..", "J": ".---",
    "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---",
    "P": ".--.", "Q": "--.-", "R": ".-.", "S": "...", "T": "-",
    "U": "..-", "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--",
    "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
    " ": "/",
    "!": "-.-.--", "?": "..--..", ".": ".-.-.-", ",": "--..--",
    "'": ".----.", '"': ".-..-.", "/": "-..-.", "(": "-.--.",
    ")": "-.--.-", "&": ".-...", ":": "---...", ";": "-.-.-.",
    "=": "-...-", "+": ".-.-.", "-": "-....-", "_": "..--.-",
    "$": "...-..-", "@": ".--.-.", "¿": "..-.-", "¡": "--...-",
}


TEXT_CODE = {value: key for key, value in MORSE_CODE.items()}


def text_to_morse(text: str) -> str:
    """Convert a string of text to Morse code, characters separated by spaces."""
    codes = []
    for char in text.upper():
        if char not in MORSE_CODE:
            raise ValueError(f"No Morse mapping for character: {char!r}")
        codes.append(MORSE_CODE[char])
    return " ".join(codes)


def morse_to_text(morse: str) -> str:
    """Convert a string of Morse code back to text.

    Letters are expected to be separated by single spaces and words by
    ``/`` (matching the output of ``text_to_morse``), so the two functions
    round-trip: ``morse_to_text(text_to_morse(s)) == s.upper()``.
    """
    words = morse.strip().split(" / ")
    decoded_words = []
    for word in words:
        letters = []
        for symbol in word.split():
            if symbol not in TEXT_CODE:
                raise ValueError(f"No text mapping for Morse symbol: {symbol!r}")
            letters.append(TEXT_CODE[symbol])
        decoded_words.append("".join(letters))
    return " ".join(decoded_words)


if __name__ == "__main__":
    message = input("Enter a message to be converted into Morse code: ")
    print(text_to_morse(message))
