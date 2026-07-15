from bs4 import BeautifulSoup

with open("data/AsciiDocLiveTemplates.xml", "r") as xmlFile:
    xmlString = "".join(xmlFile.readlines())
    xml = BeautifulSoup(xmlString, "xml")
    # print(xml.prettify())

    for templateElement in xml.find_all("template"):
        # print(templateElement)
        value = str(templateElement["value"])
        # print(value)

        for variableElement in templateElement.find_all("variable"):
            # print(variableElement)
            value = value.replace(
                "$" + variableElement["name"] + "$", variableElement["defaultValue"]
            )
        print(value)
