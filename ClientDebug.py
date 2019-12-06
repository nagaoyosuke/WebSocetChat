import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import time

import json


class Client:
    def __init__(self,userID,userName):
        self.userID = userID
        self.userName = str(userName)

    def S_Login(self, ws,):
        with open('Json/Send/Login.json') as f:
            j = json.load(f)
            userName = input('名前は? \n')

            if userName == '':
                userName = '名無し'

            j['userName'] = userName
            
            self.userName = userName

            ws.send(json.dumps(j,ensure_ascii=False))
            
    def S_Talk(self, ws, message):
        with open('Json/Send/Talk.json') as f:
            j = json.load(f)

            j['userID'] = self.userID
            j['message'] = message

            ws.send(json.dumps(j,ensure_ascii=False))

    def S_DM(self, ws, message):
        with open('Json/Send/DM.json') as f:
            j = json.load(f)

            pos = message.find(',')

            j['userID'] = self.userID
            j['userName'] = self.userName
            j['oppID'] = -2
            j['oppName'] = message[3:pos]
            j['message'] = message[pos +1:]

            ws.send(json.dumps(j,ensure_ascii=False))

    def S_MemberList(self,ws):
        with open('Json/Send/API.json') as f:
            j = json.load(f)
            j['state'] = 'MemberList'
            ws.send(json.dumps(j,ensure_ascii=False))

    def S_Log(self,ws):
        with open('Json/Send/API.json') as f:
            j = json.load(f)
            j['state'] = 'Log'
            ws.send(json.dumps(j,ensure_ascii=False))

    def R_Login(self, ws,data):
        self.userID = data['userID']
        print('あなたのユーザIDは' + self.userID + 'です \n')

    def R_Talk(self, ws,data):
        # if data[('saidID')] == self.userID:
        #     return

        print(str(data['saidName']) + '(' + str(data['saidID']) +'):' + data['message'])

    def R_DM(self, ws,data):
        if data[('saidID')] == self.userID:
            return
        print('DM@' + str(data['saidName']) + '(' + str(data['saidID']) +'):' + data['message'])

    def R_Log(self, ws,data):
        print('過去ログここから \n')
        for d in data['messages']:
            print(str(d['saidName']) + '(' + str(d['saidID']) +'):' + d['message'])

        print('\n過去ログここまで \n')

        # print('DM@' + str(data['saidName']) + '(' + str(data['saidID']) +'):' + data['message'])

    def R_MemberList(self, ws,data):
        print('参加している人　ここから \n')
        for d in data['Member']:
            print(str(d['userName']) + '(' + str(d['userID']) +')')

        print('\n参加している人 ここまで \n')

    def R_Info(self, ws,data):
        print(data['message'] + '\n')

        
client = Client(-1,"名無し")

def on_message(ws, message):
    data = json.loads(message)

    if data['state'] == 'Login':
        client.R_Login(ws,data)

    if client.userID == -1:
        return

    print(message)

    if data['state'] == None:
        return

    if data['state'] == 'Login':
        client.R_Login(ws,data)
    if data['state'] == 'Talk':
        client.R_Talk(ws,data)
    if data['state'] == 'DM':
        client.R_DM(ws,data)
    if data['state'] == 'Log':
        client.R_Log(ws,data)
    if data['state'] == 'MemberList':
        client.R_MemberList(ws,data)
    if data['state'] == 'Info':
        client.R_Info(ws,data)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    def run(*args):
        client.S_Login(ws)

        print(('end:退出 \n' + 
                'list:部屋にいる人を表示 \n' +
                'log:過去５０件分の発言を見れる \n' + 
                'dm@(相手の名前),(文章):DMを送れる \n'))

        while True:
            if client.userID == -1:
                continue

            s = input()

            if s == "end":
                break
            elif s == "list":
                client.S_MemberList(ws)
            elif s == 'log':
                client.S_Log(ws)
            elif  s[0:3] == 'dm@':
                client.S_DM(ws,s)
            else:
                client.S_Talk(ws,s)

            time.sleep(0.5)
        time.sleep(1)
        ws.close()
        print("thread terminating...")
    thread.start_new_thread(run, ())

if __name__ == "__main__":
    websocket.enableTrace(False)
    #ws = websocket.WebSocketApp("wss://pythonwebsockettest.herokuapp.com",
    ws = websocket.WebSocketApp("ws://127.0.0.1:12345",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()