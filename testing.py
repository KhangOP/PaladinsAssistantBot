import requests
from bs4 import BeautifulSoup


def get_champ_stats(player_name, champ):
    url = "https://mypaladins.com/player/" + player_name
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    print(soup)

    """
    # Get the secret number assigned to every player on their site
    for link in soup.find_all('a'):
        link = link.get('href')
        if link != "/":
            url = link.replace("pl/", "")
            break

    url = url + "/champions"
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    sup = str(soup.get_text()).splitlines()
    sup = list(filter(None, sup))
    yes = 0

    info = []

    # Gathering the info we want
    for item in sup:
        item = item.replace("/", "").strip()
        if item == champ:
            yes = 1
        if yes >= 1:
            if yes == 3 or yes == 4 or yes == 5 or yes == 7 or yes == 8:
                pass
            else:
                info.append(item)
            yes += 1
            if yes == 10:
                break

    # Here is what we want
    results = str("Champion: " + info.pop(0) + "\n" + info.pop(0) + "\n" + "KDA: " + info.pop(0) + "\n" + "WinRate: " +
                  info.pop(0))
    return results
    """


player_name = "feistyjalapeno"
champ = "Drogoz"

print(get_champ_stats(player_name, champ))

"""
print(soup.prettify())

print(soup.find_all('a'))

print(soup.find_all('div'))
"""


"""
# api-endpoint
URL = "https://mypaladins.com/player/"

playerName = "feistyjalapeno"

# defining a params dict for the parameters to be sent to the API
PARAMS = {'tabindex':1,
          'type':"search",
           'class':"js-txt-search-player form-control",
            'name': playerName}

# sending get request and saving the response as response object
r = requests.get(url=URL, params=PARAMS)

print(r)

# extracting data in json format
data = r.json()
print(data)
"""
