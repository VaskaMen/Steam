import requests
import asyncio
from flask import Flask, render_template, request, jsonify

from currency import Currency
from steamPrice import SteamPrice
from SteamDB import  SteamDB

c = Currency()
sp = SteamPrice()
sdb = SteamDB()
# sdb.add_list_game()

app = Flask(__name__)
@app.route("/", methods=["POST", "GET"])
def home():
    return render_template("linkPrice.html")


async def get_dlc(dlc):
        print(dlc)
        taskTR = asyncio.create_task(sp.GetListDlc(dlc, 'TR'))
        taskKZ = asyncio.create_task(sp.GetListDlc(dlc, 'KZ'))
        taskUS = asyncio.create_task(sp.GetListDlc(dlc, 'US'))
        taskRU = asyncio.create_task(sp.GetListDlc(dlc, 'RU'))
        await asyncio.gather(taskTR, taskKZ, taskUS, taskRU)

        return jsonify({
            'status': 0,
            'dlc_priceTR': taskTR.result(),
            'dlc_priceRU': taskRU.result(),
            'dlc_priceKZ': taskKZ.result(),
            'dlc_priceUS': taskKZ.result(),
        })




@app.route("/dlcPrice", methods=["POST", "GET"])
def dlcPrice():
    dlc = request.get_json('dlc')['dlc']
    r = asyncio.run(get_dlc(dlc)).get_json()
    return r

@app.route("/linkPrice", methods=["POST", 'GET'])
def linkPrice():
    if request.method == "POST":
        link = request.form.get("link")
        link = (sp.cutLink(link))
        if sp.chekGame(link):

            image = sp.getImage(link)

            poluchiTRY = sdb.get_game_info(link, "TR")
            poluchiRUB = sdb.get_game_info(link, "RU")
            poluchiKZT = sdb.get_game_info(link, "KZ")
            poluchiUSD = sdb.get_game_info(link,"US")
            name_game = poluchiUSD['name']

            return jsonify({
            'status': 0,
            'poluchiTRY': poluchiTRY,
            'poluchiRUB' : poluchiRUB,
            'poluchiKZT' : poluchiKZT,
            'poluchiUSD' : poluchiUSD,

            'name_game' : name_game,
            'image' : image
            })
        else:
            return jsonify({
            'status': 1,
            })

    else:
        return jsonify({
            'status': 1,
            })

app.run(debug=True)
