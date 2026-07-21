# In Python the default sort function only takes a single argument. That means
# when we have to compare a more complex data structure where the order depends
# on multiple values we have no way to compare to values to determine their
# order. Instead we can return a tuple containing the values that we want to
# order by.
people = [
    {"name": "Ana", "age": 30, "city": "London"},
    {"name": "Ben", "age": 25, "city": "Paris"},
    {"name": "Beatrice", "age": 25, "city": "Madrid"},
    {"name": "Cara", "age": 25, "city": "Berlin"},
]

people.sort(key=lambda person: (person["age"], person["name"]))
print(people)
