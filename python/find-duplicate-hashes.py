from sys import argv

if len(argv) <= 1:
    print(
        "Error: Missing argument. \n"
        + "Usage: find-duplicate-hashes.py PATH-TO-HASHLIST"
    )
    exit(1)

pathToHashFile = argv[1]

with open(f"{pathToHashFile}", mode="r", encoding="utf-8") as hashFile:
    hashesAndPaths = hashFile.readlines()
# print(hashesAndPaths)

hashList: list[str] = []
fileList: list[str] = []

for hashAndPath in hashesAndPaths:
    splitHashAndPath = hashAndPath.split(" ")
    hash = splitHashAndPath[0]
    # Collapse path in a single string in case it contained spaces
    filePath = " ".join(splitHashAndPath[1:])

    if hash in hashList:
        i = hashList.index(hash)
        dupHash = hashList[i]
        dupFile = fileList[i]

        print(
            "Found duplicate files: \n"
            + f"  {hash} -> {filePath}"
            + f"  {dupHash} -> {dupFile}"
        )
    else:
        hashList.append(hash)
        fileList.append(filePath)

print("Done")
