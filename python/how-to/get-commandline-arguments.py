from getopt import getopt
import sys


def main():
    # For short options use the colon to specify options that take an argument
    shortOptions = "he:i:"
    # For long options use the equal sign
    longOptions = ["help", "exclude=", "include="]
    argv = sys.argv  # get arguments
    print(argv)
    argv = argv[1:]

    parsedOptions, otherArgs = getopt(argv, shortOptions, longOptions)
    print(parsedOptions)
    print(otherArgs)


if __name__ == "__main__":
    main()
