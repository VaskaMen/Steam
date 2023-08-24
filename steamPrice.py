import time

import requests
from currency_converter import CurrencyConverter
from currency import Currency

class SteamPrice:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    }
    c = Currency()
    # Вернёт список все что есть в стиме
    def getAllgames(self):
        all_games_req = requests.get(f"http://api.steampowered.com/ISteamApps/GetAppList/v0002/")
        all_games_req = all_games_req.json()
        allGames = all_games_req['applist']['apps']
        return allGames

    # Вернёт полную информацию о стоимости игры
    def getFullPrice(self, game_id, currency):
        price_req = requests.get(f"https://store.steampowered.com/api/appdetails?filters=price_overview&appids={game_id}&cc={currency}")
        price_req = price_req.json()
        return price_req

    # Вернёт только конечную цену игры (Включая скидку)
    def getPriceGame(self, game_id, currency):
        price_req = requests.get(f"https://store.steampowered.com/api/appdetails?filters=price_overview&appids={game_id}&cc={currency}")
        price_req = price_req.json()
        if 'data' in price_req[f"{game_id}"]:
            if 'price_overview' in price_req[f"{game_id}"]['data']:
                price = price_req[f"{game_id}"]['data']['price_overview']['final_formatted']
                currencyGame = price_req[f"{game_id}"]['data']['price_overview']['currency']
                gamePrice = [price, currencyGame]
                return gamePrice
            else:
                return [0, 0]
        else:
            print("Price cant be find")
            return [0, 0]

    # Вернёт название игры если сможет найти
    def getNameGame(self, game_id):
        game_req = requests.get(f"https://store.steampowered.com/api/appdetails?appids={game_id}&cc=US")
        game_req = game_req.json()
        if 'data' in game_req[f'{game_id}']:
            if self.chekGame(game_id):
                game_name = game_req[f"{game_id}"]['data']['name']
                return game_name

    # Является ли данный id игрой
    def chekGame(self, game_id):
        game_req = requests.post(f"https://store.steampowered.com/api/appdetails?appids={game_id}&cc=US", headers=self.headers)
        game_req = game_req.json()
        if game_req:
            if 'data' in game_req[f'{game_id}']:
                return game_req[f'{game_id}']['data']["type"] == "game" or game_req[f'{game_id}']['data']["type"] == "dlc"
            else:
                return False
        else:
            return False


    # Возврашает первую игру которую найдёт
    def findGameFirst(self, name):
        allGames = self.getAllgames()

        for games in allGames:
            if name == games['name']:
                return games['appid']
        return -1

    def getGameInfo(self, appid, country):
        game_req = requests.get(f"https://store.steampowered.com/api/appdetails?appids={appid}&cc={country}&l=ru").json()
        game_info = {
            'type': 'Npne',
            'name': 'None',
            'currency': country,
            'initial': 0,
            'final': 0,
            'discount_percent': 0,
            'initial_formatted': 0,
            'final_formatted': 0
        }
        if game_req != None:
            if game_req[f'{appid}']['success']:
                game_info['type']= game_req[f'{appid}']['data']['type']
                game_info['name']= game_req[f'{appid}']['data']['name']

                if 'dlc' in game_req[f'{appid}']['data']:
                    game_info['dlc'] = game_req[f'{appid}']['data']['dlc']

                if game_req[f'{appid}']['data']['is_free'] == False and 'price_overview' in game_req[f'{appid}']['data']:
                    game_info['currency'] = game_req[f'{appid}']['data']['price_overview']['currency']
                    currency = game_info['currency']
                    game_info['initial'] = game_req[f'{appid}']['data']['price_overview']['initial']
                    game_info['final'] = game_req[f'{appid}']['data']['price_overview']['final']
                    game_info['discount_percent'] = game_req[f'{appid}']['data']['price_overview']['final']
                    game_info['initial_formatted'] = game_req[f'{appid}']['data']['price_overview']['initial_formatted']
                    game_info['final_formatted'] = game_req[f'{appid}']['data']['price_overview']['final_formatted']
                    if currency != 'RUB':
                        game_info[f'poluchi{currency}_RUB'] = self.c.cumvert(self.c.priceToFloat(game_info['final_formatted']), currency)
                    else:
                        game_info[f'poluchi{currency}_RUB'] = currency

        return game_info

    async def GetListDlc(self, listdlc, country):
        currency_list = {
            'TR': "TRY",
            'KZ': 'KZT',
            'US': 'USD',
            'RU': 'RUB'
        }
        currency = currency_list[f'{country}']
        t = time.time()
        name_get = requests.get("http://api.steampowered.com/ISteamApps/GetAppList/v0002/")
        name_get = name_get.json()
        dlc_get = requests.get(
            f"http://store.steampowered.com/api/appdetails/?filters=price_overview&appids={','.join(map(str, listdlc))}&cc={country}")
        dlc_get = dlc_get.json()

        dlc_info = {}
        dlc_name = {}
        dlc_mas = [dls for dls in listdlc]

        for j in name_get['applist']['apps']:
            if j['appid'] in dlc_mas:
                dlc_name[f"{j['appid']}"] = j['name']

        for i in dlc_get:

            if f'{i}' in dlc_name:
                name = dlc_name[f'{i}']
            else:
                name = "Not found"
            if 'price_overview' in dlc_get[f'{i}']['data'] and dlc_get[f'{i}']['data']['price_overview']['final_formatted'] != 'Free':

                dlc_info[f'{i}'] = {
                    'name': name,
                    'currency': currency,
                    'initial': dlc_get[f'{i}']['data']['price_overview']['initial'],
                    'final': dlc_get[f'{i}']['data']['price_overview']['final'],
                    'discount_percent': dlc_get[f'{i}']['data']['price_overview']['final'],
                    'initial_formatted': dlc_get[f'{i}']['data']['price_overview']['initial_formatted'],
                    'final_formatted': dlc_get[f'{i}']['data']['price_overview']['final_formatted'],
                    f'poluchi{currency}_RUB': 0
                }
                if currency != 'RUB':
                    dlc_info[f'{i}'][f'poluchi{currency}_RUB'] = self.c.cumvert(dlc_get[f'{i}']['data']['price_overview']['final_formatted'], currency)
                else:
                    dlc_info[f'{i}'][f'poluchi{currency}_RUB'] = dlc_get[f'{i}']['data']['price_overview']['final_formatted']
            else:
                dlc_info[f'{i}'] = {
                    'name': name,
                    "currency": currency,
                    'initial': 0,
                    'final': 0,
                    'discount_percent': 0,
                    'initial_formatted': 0,
                    'final_formatted': 0,
                    f'poluchi{currency}_RUB': 0
                }
        return dlc_info

    def cutLink(self, link):
        try:
            a = link.find("app/") + 4
            if link[:a] == "https://store.steampowered.com/app/":
                linka = link[a:link.find("/",a)]
                return linka
            else:
                return None
        except:
            return None


    def getImage(self, game_id):
        game_req = requests.get(f"https://store.steampowered.com/api/appdetails?appids={game_id}&cc=US")
        game_req = game_req.json()
        return (game_req[f"{game_id}"]["data"]["header_image"])




    # Возврашет список id игр где совпадают имена
    # def findGameAll(self, name):
    #     allGames = self.getAllgames()
    #     matchGames = []
    #
    #     for game in allGames:
    #         if str(name).lower() in str(game['name']).lower():
    #             if self.chekGame(game['appid']):
    #                 matchGames.append(game['appid'])
    #
    #     return matchGames