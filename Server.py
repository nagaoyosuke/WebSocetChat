#Heroku用　ローカル環境で試したいときはLocalServer.pyを起動

import logging
import psycopg2
import os

from websocket_server import WebsocketServer
 
from bottle import route, run

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(' %(module)s -  %(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
 
# Callback functions
 
 #新しいクライアントが接続
def new_client(client, server):
    logger.info('New client {}:{} has joined.'.format(client['address'][0], client['address'][1]))
    server.clients[-1]['name'] = "名無しさん" + (str(client['id']))
    server.send_message_to_all(server.clients[-1]['name'] + "が入室しました")

#クライアントの接続がきれた
def client_left(client, server):
    logger.info('Client {}:{} has left.'.format(client['address'][0], client['address'][1]))
    server.send_message_to_all(str(getNickNameFromID(server,client['id'])) + ":が退出しました")

#クライアントからメッセージを受信
def message_received(client, server, message):
    l = len(message)

    print(message)
    server.send_message(client,"RecivedMessage Success!!12345")

    #接続中の人たち
    if message == "clients":
        ClientsList(client, server, message)
        return

    #ニックネームを設定
    sub = message.find("@")
    if sub > -1 and sub < l - 1:
        NickNameSet(client, server, message,sub)

    #DM機能
    sub = message.find("<")
    if sub > -1   and sub < l - 1:
        DirectMessage(client, server, message,sub)
        return
    else:
        server.send_message_to_all(str(getNickNameFromID(server,client['id'])) + ":" + message[sub + 1:])
    # logger.info('Message "{}" has been received from {}:{}'.format(message, client['address'][0], client['address'][1]))
    # reply_message = 'Hi! ' + message
    # server.send_message(client, reply_message)
    # logger.info('Message "{}" has been sent to {}:{}'.format(reply_message, client['address'][0], client['address'][1]))

#接続中の人たち
def ClientsList(client, server, message):
    logger.info(server.clients)

    s = "今いる人たち\n"

    for i in server.clients:
        s += i['name'] + "\n"

    s += "以上"

    server.send_message(client, s)
#ニックネームを設定
def NickNameSet(client, server, message,sub):
    name = message[sub + 1:]
    server.clients[client['id'] - 1]['name'] = name

#DM機能
def DirectMessage(client, server, message,sub):
    SendClientName = message[0:sub]
    try:
        #server.send_message(server.clients[(int)(SendClientID) - 1], str(client['id']) + ":" + message[sub + 1:])
        SendClient = getDataFromNickName(server,SendClientName)
        server.send_message(server.clients[SendClient], str(getNickNameFromID(server,client['id'])) + ":" + message[sub + 1:])
    except:
        logger.error("NotID")
        server.send_message(client, "その人は居ないよ")

def getDataFromNickName(server,name):
    c = 0
    for i in server.clients:
        if i['name'] == name:
            return c
        c += 1
def getNickNameFromID(server,id):
    for i in server.clients:
        if i['id'] == id:
            return i['name']

@route('/')
def hello():
    print("hello")
    return ""

# Main
if __name__ == "__main__":
    server = WebsocketServer(port=int(os.getenv("PORT", 5000)), host='0.0.0.0')
    server.set_fn_new_client(new_client)
    server.set_fn_client_left(client_left)
    server.set_fn_message_received(message_received)
    server.run_forever()