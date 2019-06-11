from pyrez.api import PaladinsAPI

file_name = "token"
# Gets ID and KEY from a file
with open(file_name, 'r') as f:
    TOKEN = f.readline().strip()    # Does nothing
    PREFIX = f.readline()           # Does nothing
    ID = int(f.readline())
    KEY = f.readline()
f.close()

paladinsAPI = PaladinsAPI(devId=ID, authKey=KEY)

"""
try:
    player = paladinsAPI.getPlayer("Bubbles")
    print(player)
    player = paladinsAPI.getPlayerId("Bubbles", "22")
    player = paladinsAPI.getPlayer(player[0].playerId)
    print(player)
except BaseException:
    print("could not find")
"""
print("\33[91{}\33[0m".format("red?"))
print("hi")
