# def formatCapitalize(name):
#     return name.capitalize()

# nome = 'LEONARDO MENDONCA'

# nome = nome.split(' ')

# textFormated = ' '.join(list(map(formatCapitalize , nome)))

# print(textFormated)

def formatCapitalize(fullName):
    return ' '.join(list(map(lambda x: x.capitalize() , fullName.split())))

print(formatCapitalize('Leonardo Mendonca'))