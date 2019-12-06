#ローカル用


import logging
import psycopg2
import os
import json
import random

from websocket_server import WebsocketServer
 
from bottle import route, run

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(' %(module)s -  %(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
 
# Callback functions

class MemberBase:

    def __init__(self,client,server,userID,userName):
        self.client = client
        self.server = server
        self.userID = userID
        self.userName = str(userName)

class RoomBase:

    def __init__(self, maxUser,maxLog):
        self.maxUser = maxUser
        self.Member = []
        self.maxLog = maxLog
        self.logs = [''] * maxLog
        # self.logs = dict([('state', 'Talk'), ('saidID', -1),('saidName', 'hoge'), ('message', 'tya')]) * self.maxLog

    def __handler(self,func,*args):
        return func(*args)

    #Nullチェック
    def MemberCheck(self,func,arg):
        if func != None:
            my = self.__handler(func,arg)
            if my == None:
                #sendData = dict([('state', 'Error'), ('message', str(ErrMessage))])
                #sendData = dict([('state', 'Error'), ('message', 'You donot join Member in Room')])
                #server.send_message(client,json.dumps(sendData))
                return False
        return True

    def Login(self, client, server, data):
        _usrid = random.randint(1,5000)
        m = MemberBase(client,server,_usrid,data['userName'])
        self.Member.append(m)
        sendData = dict([('state', 'Login'), ('userID', str(_usrid))])
        server.send_message(client,json.dumps(sendData,ensure_ascii=False))
        sendData = dict([('state', 'Info'), ('message', str(m.userName) + 'さんが入室しました')])
        server.send_message_to_all(json.dumps(sendData,ensure_ascii=False))

    def RoomMemberList(self, client, server, data):
        base = dict([('userID',-1), ('userName','Hoge')])
        sendData = {"state": "MemberList","Member": []}

        # sendData.append(dict([('state','MemberList')]))
        # sendData.append('state')
        # sendData.append('MemberList')

        for m in self.Member:

            b = base.copy()
            b['userID'] = m.userID
            b['userName'] = m.userName
            sendData['Member'].append(b)
        
        print(sendData)
        server.send_message(client,json.dumps(sendData,ensure_ascii=False))

    def Talk(self, client, server, data):

        if self.MemberCheck(self.GetFindMemberFromClient,client) == False:
            sendData = dict([('state', 'Error'), ('message', 'You donot join Member in Room')])
            server.send_message(client,json.dumps(sendData,ensure_ascii=False))
            return

        my = self.GetFindMemberFromClient(client)

        sendData = dict([('state', 'Talk'), ('saidID', my.userID),('saidName', my.userName), ('message', data['message'])])
        server.send_message_to_all(json.dumps(sendData,ensure_ascii=False))
        print(str(sendData['saidName']) + '(' + str(sendData['saidID']) +'):' + sendData['message'])
        self.logs.pop(0)
        self.logs.append(sendData)

    def DMRequest(self, client, server, data):
        #Nullチェック
        #n = self.MatchingMemberCheck(client,server,self.GetFindMemberFromClient,client,self.GetFindMemberFromUserID,data['oppID'])
        # if n == False:
        #     return

        if self.MemberCheck(self.GetFindMemberFromClient,client) == False:
            sendData = dict([('state', 'Error'), ('message', 'You donot join Member in Room')])
            server.send_message(client,json.dumps(sendData,ensure_ascii=False))
            return

        if self.MemberCheck(self.GetFindMemberFromUserName,data['oppName']) == False:
            sendData = dict([('state', 'Error'), ('message', 'Opponent donot join Member in Room')])
            server.send_message(client,json.dumps(sendData,ensure_ascii=False))
            return

        my = self.GetFindMemberFromClient(client)
        opp = self.GetFindMemberFromUserName(data['oppName'])
        
        sendData = dict([('state', 'DM'), ('saidID', my.userID),('saidName', my.userName), ('message', data['message'])])
        server.send_message(opp.client,json.dumps(sendData,ensure_ascii=False))

    def LogRequest(self,client, server, data):
        base = dict([('saidID',''), ('saidName','Hoge'), ('message','Hoge')])
        sendData = {"state": "Log","messages": []}

        # sendData.append(dict([('state','MemberList')]))
        # sendData.append('state')
        # sendData.append('MemberList')

        for m in self.logs:

            if m == '':
                continue

            b = base.copy()

            b['saidID'] = m['saidID']
            b['saidName'] = m['saidName']
            b['message'] = m['message']
            sendData['messages'].append(b)
        
        print(sendData)
        server.send_message(client,json.dumps(sendData,ensure_ascii=False))


    def Logout(self,client,server):

        print("Logout")
        logoutUser = self.GetFindMemberFromClient(client)        
        sendData = dict([('state', 'Info'), ('message', logoutUser.userName + 'がログアウトしました。')])

        server.send_message_to_all(json.dumps(sendData,ensure_ascii=False))  

        self.Member.remove(logoutUser)        
      
    def GetFindMemberFromClient(self,client):
        for value in self.Member:
            if value.client == client:
                return value
        return None

    def GetFindMemberFromUserID(self,userID):
        for value in self.Member:
            if str(value.userID) == str(userID):
                return value
        return None

    def GetFindMemberFromUserName(self,userName):
        for value in self.Member:
            if str(value.userName) == str(userName):
                return value
        return None

Room = RoomBase(16,50)

 #新しいクライアントが接続
def new_client(client, server):
    logger.info('New client {}:{} has joined.'.format(client['address'][0], client['address'][1]))
    server.clients[-1]['name'] = (str(client['id']))
    sendData = dict([('state', 'Info'), ('message', server.clients[-1]['name'] + "が入室しました")])
    # server.send_message_to_all(json.dumps(sendData,ensure_ascii=False))

#クライアントの接続がきれた
def client_left(client, server):
    logger.info('Client {}:{} has left.'.format(client['address'][0], client['address'][1]))
    # server.send_message_to_all(str(getNickNameFromID(server,client['id'])) + "が退出しました")
    Room.Logout(client,server)
    
#クライアントからメッセージを受信
def message_received(client, server, message):

    data = json.loads(message)

    # print(data['state'])

    if data['state'] == 'Init':
        sendData = InitMessage(data)
    elif data['state'] == 'Talk':
        Room.Talk(client,server,data)
    elif data['state'] == 'Login':
        Room.Login(client,server,data)
    elif data['state'] == 'DM':
        Room.DMRequest(client,server,data)
    elif data['state'] == 'MemberList':
        Room.RoomMemberList(client,server,data)
    elif data['state'] == 'Log':
        Room.LogRequest(client,server,data)

    # sendID = getSendID(int(client['id']))
    # server.send_message(server.clients[sendID],json.dumps(sendData))
   
@route('/')
def hello():
    print("hello")
    return ""

# Main
if __name__ == "__main__":
    server = WebsocketServer(port=12345, host='127.0.0.1', loglevel=logging.INFO)
    server.set_fn_new_client(new_client)
    server.set_fn_client_left(client_left)
    server.set_fn_message_received(message_received)
    server.run_forever()