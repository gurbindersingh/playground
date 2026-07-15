import re as regex

# Regex module tutorial: https://docs.python.org/3/howto/regex.html

inputFile = "data/cities_alphanum.txt"
outputFile = "out/cities-alphanum.txt"

with open(inputFile, "r", encoding="utf-8") as sourceFile:
    with open(outputFile, "w", encoding="utf-8") as outFile:
        brackets = regex.compile("\(|\)|[|]")
        numbers = regex.compile("\d+")
        allCaps = regex.compile("[A-Z]{2,}")
        specialSymbols = regex.compile('(_)+|(-)+|(!)+|(")+|(#)+|(.)+|(&)+|(/)+')

        counter = 100
        for line in sourceFile.readlines():
            print("---------------------------------------------------")
            transformedString = line.replace("(historical)", "")
            print("After stripping '(historical)':" + transformedString)

            transformedString = transformedString.replace("(former)", "")
            print("After stripping '(former)':" + transformedString)

            transformedString = brackets.sub("", transformedString)
            print("After :" + transformedString)

            transformedString = specialSymbols.sub("", transformedString)
            print("After :" + transformedString)

            transformedString = numbers.sub("", transformedString)
            print("After :" + transformedString)

            transformedString = allCaps.sub("", transformedString)
            print("After :" + transformedString)

            transformedString = transformedString.strip()
            print("After :" + transformedString)
            print("---------------------------------------------------")

            counter -= 1
            if counter < 0:
                break

            # if(len(transformedString) > 0):
            # print(f"{line} -> {transformedString}")
            outFile.write(transformedString + "\n")
