import requests

imageFilename = "unsplash.jpg"
imagePath = "out/" + imageFilename
with open(imagePath, "wb") as image:
    # Get the image from Unsplash and write it to the filesystem
    response = requests.get("https://source.unsplash.com/random/?cute-animals,cat")
    if not response.ok:
        print("Request to Unsplash did no succeed.")
        exit(-1)
    image.write(response.content)
