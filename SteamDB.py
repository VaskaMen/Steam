# import sqlite3
import time
import requests
from datetime import  datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from  currency import  Currency

coun_cur = {
    'TR': 'TRY',
    'RU': 'RUB',
    'KZ': 'KZT',
    'US': 'USD'
}

# cursor.execute(
#         """CREATE TABLE IF NOT EXISTS apps
#         (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         app_id INTEGER PRIMARY KEY,
#         app_name TEXT
#         )
#         """)
con = create_engine("sqlite:///SteamPrice.db")
Session = sessionmaker(bind=con)
class SteamDB:
    cursor = Session()
    c = Currency()
    def add_list_game(self):
        all_games_req = requests.get(f"http://api.steampowered.com/ISteamApps/GetAppList/v0002/")
        all_games_req = all_games_req.json()
        allGames = all_games_req['applist']['apps']
        for a in allGames:
            game = (a['appid'], f"{a['name']}")
            self.cursor.execute(f"INSERT OR IGNORE INTO apps (app_id, app_name) VALUES (?, ?)", game)
        self.con.commit()


    def create_price_table(self, country):
        self.cursor.execute(
            f"""CREATE TABLE IF NOT EXISTS price_{country}
            (
            app_id INTEGER,
            initial INTEGER,
            initial_formatted VARCHAR(50),
            discount_percent INTEGER,
            final INTEGER,
            final_formatted VARCHAR(50),
            date DATE
            )
            """
        )

    def priceRub(self, countru):
        self.create_price_table(countru)
        all_games_req = requests.get(f"http://api.steampowered.com/ISteamApps/GetAppList/v0002/").json()
        allGames = all_games_req['applist']['apps']
        step = 900

        apps = []
        for a in allGames:
            apps.append(a['appid'])


        for i in range(0, len(apps), step):

            if i + step > len(apps):
                end = len(apps) - 1
            else:
                end = i + step


            pros = round((i/len(apps)) * 100, 3)


            print(f"{'{:.3f}'.format(pros)}% [{'▬' * int((pros/5))}{'•' * int(((100 - pros)/5))}] {countru}")

            price_list = requests.get(
                f"http://store.steampowered.com/api/appdetails/?filters=price_overview&"
                f"appids={','.join(map(str, apps[i:end] ))}&cc={countru}")

            # Заполнение таблицы
            if price_list.status_code == 200:
                price_list = price_list.json()
                for game in price_list:
                    if game in price_list and price_list[f'{game}']['success'] and price_list[f'{game}']['data'] != []:
                        price_overview = price_list[f'{game}']['data']['price_overview']
                        if self.diferent_price(game, countru, price_overview):
                            self.add_game(countru,
                                     game,
                                     price_overview['initial'],
                                     price_overview['initial_formatted'],
                                     price_overview['discount_percent'],
                                     price_overview['final'],
                                     price_overview['final_formatted']
                                     )
                    else:
                        price_overview = {
                                'initial': 0,
                                'discount_percent': 0,
                                'final': 0
                        }
                        if self.diferent_price(game, countru, price_overview):
                            self.add_game(countru, game)

            else:
                print("#############################ERROR")
                time.sleep(20)


    def add_game(self, country, app_id, initial=0, initial_formatted='', discount_percent=0, final=0, final_formatted=''):
        self.cursor.execute(f"""INSERT INTO price_{country} VALUES (
                                                   {app_id},
                                                   {initial},
                                                   '{initial_formatted}',
                                                   {discount_percent},
                                                   {final},
                                                   '{final_formatted}',
                                                   '{datetime.today().strftime("%d.%m.%Y")}'
                                                   )""")
        self.con.commit()

    def last_price(self, app_id, country):
        q = text(f"SELECT * FROM price_{country} WHERE app_id = {app_id} ORDER BY date DESC LIMIT 1")
        result = self.cursor.execute(q).fetchall()
        if result != []:
            result = result[0]
            return {
                    'currency': country,
                    'app_id': result[0],
                    'initial': result[1],
                    'initial_formatted': result[2],
                    'discount_percent': result[3],
                    'final': result[4],
                    'final_formatted': result[5],
                    'date': result[6]
                }

    def get_game_info(self, app_id, country):
        cur = coun_cur[f'{country}']
        price_list = self.last_price(app_id, country)
        q = text(f"SELECT * FROM apps WHERE app_id = {app_id} LIMIT 1")
        result = self.cursor.execute(q).fetchall()
        if result != []:
            price_list['name'] = result[0][1]
            price_list['type'] = 'None'  # Coming soon
            if cur != 'RUB':
                price_list[f'poluchi{cur}_RUB'] = self.c.cumvert(self.c.priceToFloat(price_list['final_formatted']), cur)
        else:
            price_list['name'] = 'None'
            price_list['type'] = 'None'  # Coming soon
        return price_list

    def diferent_price(self, app_id, country, price_overview):
        game = self.last_price(app_id, country)
        if game != None:
            initial = game['initial'] != price_overview['initial']
            discount_percent = game['discount_percent'] != price_overview['discount_percent']
            final = game['final'] != price_overview['final']
            if initial and discount_percent and final:
                return True
            else: return False
        else:
            return False

