import csv


inputFilePath = "data/timesheet_x.csv"
outputFilePath = "out/timesheet_x.out.csv"

with open(inputFilePath, mode="r") as inputCsvFile:
    with open(outputFilePath, mode="w") as outputCsvFile:
        csvReader = csv.reader(inputCsvFile, delimiter=";", quotechar='"')
        csvWriter = csv.writer(outputCsvFile, delimiter=";", quotechar='"')

        for row in csvReader:
            csvWriter.writerow([x.replace("x", "y") for x in row])
