import time
import requests
from datetime import  datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import asyncio
import currency
import threading
# from  currency import  Currency

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

class SteamDB:
    con = create_engine("sqlite:///SteamPrice.db", pool_size=20, pool_timeout=240)
    Session = sessionmaker(bind=con)
    cursor = Session()

    c = currency.Currency()
    def add_list_game(self):
        all_games_req = requests.get(f"http://api.steampowered.com/ISteamApps/GetAppList/v0002/")
        all_games_req = all_games_req.json()
        allGames = all_games_req['applist']['apps']
        for a in allGames:
            game = {"app_id": a['appid'], "app_name": f"{a['name']}"}
            self.cursor.execute(text(f"INSERT OR IGNORE INTO apps (app_id, app_name) VALUES (:app_id, :app_name)"), game)
        self.con.connect().commit()

    def create_price_table(self, country):
        # 2 чтрочки чтобы открыть сессию
        Session = sessionmaker(bind=self.con)
        cursor = Session()
        cursor.execute(text(
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
        ))
        cursor.close()

    async def update_price_list(self, countru, start=0, kon=0):
        Session = sessionmaker(bind=self.con)
        cursor = Session()
        self.create_price_table(countru)
        all_games_req = requests.get(f"http://api.steampowered.com/ISteamApps/GetAppList/v0002/").json()
        allGames = all_games_req['applist']['apps']
        step = 900

        # забираем все игры
        apps = []
        for a in allGames:
            apps.append(a['appid'])

        # список актуальных цен
        all_price = self.all_last_price(countru)

        if kon == 0:
            kon = len(apps)

        for i in range(0+start, kon, step):

            if i + step > kon:
                end = kon - 1
            else:
                end = i + step

            pros = round((i/kon) * 100, 3)
            print(f"{'{:.3f}'.format(pros)}% [{'▬' * int((pros/5))}{'•' * int(((100 - pros)/5))}] {countru}")

            status_code = 0
            attempt = 0

            while status_code != 200 or attempt > 60:
                price_list = await asyncio.to_thread(requests.get,
                    f"http://store.steampowered.com/api/appdetails/?filters=price_overview&"
                    f"appids={','.join(map(str, apps[i:end] ))}&cc={countru}")
                status_code = price_list.status_code
                if status_code != 200:
                    print(f"Попытка перевызова {i}:{end} | {countru} #{attempt}")
                    await asyncio.to_thread(time.sleep, 10 + attempt)
                    attempt += 1
                else:
                    attempt = 0

            # Заполнение таблицы
            if price_list.status_code == 200:
                price_list = price_list.json()
                for game in price_list:
                    if game in price_list and price_list[f'{game}']['success'] and price_list[f'{game}']['data'] != []:
                        price_overview = price_list[f'{game}']['data']['price_overview']
                        if self.diferent_price(game, price_overview, all_price):
                            print(f"Игра обновлена: {game} | {countru}")
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
                        if self.diferent_price(game, price_overview, all_price):
                            self.add_game(countru, game)

            else:
                print("#############################ERROR")
            cursor.close()

    def async_update_update_price_list(self, countrys=['RU', 'TR', 'US', 'KZ']):
        async def __update():
            tasks = []
            for country in countrys:
                task = asyncio.create_task(self.update_price_list(country))
                tasks.append(task)
            await asyncio.gather(*tasks)

        asyncio.run(__update())

    def add_game(self, country, app_id, initial=0, initial_formatted='', discount_percent=0, final=0, final_formatted=''):
        Session = sessionmaker(bind=self.con)
        cursor = Session()
        cursor.execute(text(f"""INSERT INTO price_{country} VALUES (
                                                   {app_id},
                                                   {initial},
                                                   '{initial_formatted}',
                                                   {discount_percent},
                                                   {final},
                                                   '{final_formatted}',
                                                   '{datetime.today().strftime("%d.%m.%Y")}'
                                                   )"""))
        cursor.commit()
        cursor.close()

    def all_last_price(self, country):
        full_price_list = {}
        Session = sessionmaker(bind=self.con)
        cursor = Session()
        q = text(f"select app_id, initial, initial_formatted, discount_percent, final, final_formatted, max(date) from price_{country} group by app_id")
        results = cursor.execute(q).fetchall()
        cursor.close()
        if results != []:
            for i in results:
                result = i
                full_price_list[f'{result[0]}'] = {
                        'currency': country,
                        'app_id': result[0],
                        'initial': result[1],
                        'initial_formatted': result[2],
                        'discount_percent': result[3],
                        'final': result[4],
                        'final_formatted': result[5],
                        'date': result[6]
                    }

        return full_price_list


    def last_price(self, app_id, country):
        Session = sessionmaker(bind=self.con)
        cursor = Session()
        q = text(f"SELECT * FROM price_{country} WHERE app_id = {app_id} ORDER BY date DESC LIMIT 1")
        result = cursor.execute(q).fetchall()
        cursor.close()
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
            price_list['name'] = result[0][2]
            price_list['type'] = 'None'  # Coming soon
            if cur != 'RUB':
                price_list[f'poluchi{cur}_RUB'] = self.c.cumvert(self.c.priceToFloat(price_list['final_formatted']), cur)
        else:
            price_list['name'] = 'None'
            price_list['type'] = 'None'  # Coming soon
        return price_list

    # def diferent_price(self, app_id, country, price_overview):
    #     game = self.last_price(app_id, country)
    #     if game != None:
    #         initial = game['initial'] != price_overview['initial']
    #         discount_percent = game['discount_percent'] != price_overview['discount_percent']
    #         final = game['final'] != price_overview['final']
    #         if initial and discount_percent and final:
    #             return True
    #     return False

    def diferent_price(self, app_id, price_overview, price_list):
        if app_id in price_list:
            initial = price_list[f'{app_id}']['initial'] != price_overview['initial']
            discount_percent = price_list[f'{app_id}']['discount_percent'] != price_overview['discount_percent']
            final = price_list[f'{app_id}']['final'] != price_overview['final']
            if initial and discount_percent and final:
                return True
            else:
                return False
        else:
            return True
