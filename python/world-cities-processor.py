import re as regex
from math import floor


def extractCities(inputFile: str, outputFile: str):
    print("> Extracting cities")

    with open(inputFile, "r", encoding="utf-8") as fileWithAllData:
        with open(outputFile, "w", encoding="utf-8") as fileWithOnlyCities:
            lines = fileWithAllData.readlines()
            numberOfLines = len(lines)
            progress = 0
            oldProgressBar = ""

            for line in lines:
                fileWithOnlyCities.write(line.split("\t")[1] + "\n")
                progress += 1

                newProgressBar = getProgressBar(numberOfLines, progress)
                if newProgressBar != oldProgressBar:
                    print("Progress: " + newProgressBar)
                    oldProgressBar = newProgressBar


def sortCities(inputFile: str, outputFile: str):
    print("> Sorting cities")

    with open(inputFile, "r", encoding="utf-8") as fileWithUnsortedCities:
        with open(outputFile, "w", encoding="utf-8") as fileWithSortedCities:
            lines = sorted(fileWithUnsortedCities.readlines())
            fileWithSortedCities.write("".join(lines))


def removeDuplicates(inputFile: str, outputFile: str):
    print("> Removing duplicates")

    with open(inputFile, "r", encoding="utf-8") as fileWithDuplicates:
        with open(outputFile, "w", encoding="utf-8") as fileWithoutDuplicates:
            lines = fileWithDuplicates.readlines()
            lines = list(set(lines))
            fileWithoutDuplicates.write("".join(lines))


def stripUnnecessaryCharacters(inputFile: str, outputFile: str):
    print("> Removing unnecessary characters")

    with open(inputFile, "r", encoding="utf-8") as sourceFile:
        with open(outputFile, "w", encoding="utf-8") as outFile:
            numbers = regex.compile(r"\d+")
            allCaps = regex.compile(r"[A-Z]{2,}|([A-Z]\s+)")
            specialSymbols = regex.compile(
                r"(_)+|(-)+|(!)+|(\")+|(#)+|(\.)+|(&)+|(/)+|@+|\*+|%+"
            )
            # precedingSymbols = regex.compile(r"^")
            multipleSpaces = regex.compile(r"( ){2,}")

            # counter = 100
            cities = sourceFile.readlines()
            numberOfCities = len(cities)
            progress = 0
            oldProgressBar = ""

            for line in cities:
                transformedString = (
                    line.replace("(historical)", "")
                    .replace("(former)", "")
                    .replace("(", "")
                    .replace(")", "")
                    .replace("[", "")
                    .replace("]", "")
                    .replace("{", "")
                    .replace("}", "")
                )
                transformedString = specialSymbols.sub("", transformedString)
                transformedString = numbers.sub("", transformedString)
                transformedString = allCaps.sub("", transformedString)
                transformedString = multipleSpaces.sub(" ", transformedString)
                # transformedString = precedingSymbols.sub("", transformedString)
                transformedString = transformedString.strip()

                if len(transformedString) > 0:
                    outFile.write(transformedString + "\n")

                progress += 1
                newProgressBar = getProgressBar(numberOfCities, progress)
                if newProgressBar != oldProgressBar:
                    print("Progress: " + newProgressBar)
                    oldProgressBar = newProgressBar


def getProgressBar(total: int, current: int) -> str:
    steps = total / 100
    progress = floor(current / steps)
    progressBar = "["

    for i in range(1, 100):
        if progress >= i:
            progressBar += "#"
        else:
            progressBar += " "
    return progressBar + "]"


inputFile = "data/local/cities500.txt"
outputFile = inputFile.replace("data/local", "out/cities")
extractCities(inputFile, outputFile)

inputFile = outputFile
outputFile = inputFile.replace(".txt", "-stripped.txt")
stripUnnecessaryCharacters(inputFile, outputFile)

inputFile = outputFile
outputFile = inputFile.replace(".txt", "-no_duplicates.txt")
removeDuplicates(inputFile, outputFile)

inputFile = outputFile
outputFile = inputFile.replace(".txt", "-sorted.txt")
sortCities(inputFile, outputFile)
