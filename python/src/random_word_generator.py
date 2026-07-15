from random import randrange
import sys
from typing import Final

# =============================================================================
# Globals
# =============================================================================
minLength: Final = 5
maxLength: Final = 20
wordLength: Final = randrange(minLength, maxLength + 1)
alphabet: Final = [
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
    "'",
]
vocals: Final = ["a", "e", "i", "o", "u"]
# =============================================================================
# This is just to add a newline before the output
print("")

if len(sys.argv) < 2:
    print("Usage: random-word-generator.py NUM_OF_WORDS")
    exit(1)


def lastTwoAreTheSame(picks: list[str], newPick: str) -> bool:
    return picks[-2:].count(newPick) >= 2


def chooseToTakeRandomly(picks: list[str], newPick: str) -> bool:
    threshold = 0

    if (picks[-1] in vocals and newPick in vocals) or (
        picks[-1] not in vocals and newPick not in vocals
    ):
        threshold = 5
    elif picks[-1] not in vocals and (newPick in vocals or newPick in ["h", "y"]):
        threshold = 90

    # Roll a d100
    diceRoll = randrange(0, 100)
    return diceRoll >= threshold


# =============================================================================
# Generate n words
n = int(sys.argv[1])

for _ in range(n):
    picks: list[str] = []

    while len(picks) < wordLength:
        randomIndex = randrange(len(alphabet))
        newPick = alphabet[randomIndex]
        numOfPicks = len(picks)

        # Append the letter to the word if:
        # - the word is empty and the pick is not an apostrophe
        # - the newly picked letter does not already have two successive occurrences
        # - does not already occur if it is an apostrophe
        # TODO: add a probability for choosing a consonant if the last letter is
        # also one make exceptions for h and y
        selectLetter = False
        if newPick == "'":
            selectLetter = all(
                [
                    len(picks) >= 2,
                    len(picks) < (wordLength - 3),
                    picks.count("'") < 1,
                ]
            )
        else:
            selectLetter = (len(picks) < 1) or (
                not lastTwoAreTheSame(picks, newPick)
                and chooseToTakeRandomly(picks, newPick)
            )
        if selectLetter:
            picks.append(newPick)

    print("".join(picks))
print("")
