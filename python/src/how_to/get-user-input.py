x = ""
while x != "n" and x != "y":
    x = input("Exit early (y/n)? ")

if x == "y":
    print("Exiting early!")
    exit()

print("Answer was no!")
