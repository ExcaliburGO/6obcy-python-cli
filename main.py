#!/usr/bin/python
import json
import base64
from threading import Timer, Thread
import websocket
from twocaptcha import TwoCaptcha
import queue
import time
import os
import beepy
import sys
solver = TwoCaptcha(sys.argv[1])
INITIAL_MESSAGE = "m 18"
def date():
	return str(round(time.time() * 1000))
class Client:
	ceid=1
	ckey=""
	istalk=False
	msgqueue=queue.Queue()
	captchaTries=0
	logfile="logs/unknown.txt"
	def ping(self):
		self.ws.send("2")
		Timer(self.pingInterval/1000, self.ping).start()
	def solve_captcha(self):
		self.captchaTries+=1
		try:
			result = solver.normal(self.captcha_file)
			self.captchaId=result["captchaId"]
			self.captchaCode=result["code"]
			payload={}
			payload["ev_name"]="_capsol"
			payload["ev_data"]={}
			payload["ev_data"]["solution"]=self.captchaCode
			self.ws.send("4"+json.dumps(payload))
		except:
			self.solve_captcha()
	def setTyping(self, typing):
		payload={}
		payload["ev_name"]="_mtyp"
		payload["ev_data"]={}
		payload["ev_data"]["ckey"]=self.ckey
		payload["ev_data"]["val"]=typing
		self.ws.send("4"+json.dumps(payload))
	def startSearch(self):
		self.ws.send('4{"ev_name":"_sas","ev_data":{"channel":"main","myself":{"sex":0,"loc":4},"preferences":{"sex":0,"loc":4}},"ceid":'+str(self.ceid)+'}')
		self.ceid+=1
	def sendMessage(self, msg):
		if self.istalk:
			with open(self.logfile, "a+") as f:
				f.write("> "+msg+"\n")
			payload={}
			payload["ev_name"]="_pmsg"
			payload["ev_data"]={}
			payload["ev_data"]["ckey"]=self.ckey
			payload["ev_data"]["idn"]=self.idn
			payload["ev_data"]["msg"]=msg
			payload["ceid"]=self.ceid
			self.ceid+=1
			self.idn+=1
			self.ws.send("4"+json.dumps(payload))
			self.setTyping(False)
		else:
			self.msgqueue.put(msg)
	def endTalk(self):
		self.msgqueue=queue.Queue()
		if self.istalk:
			payload={}
			payload["ev_name"]="_distalk"
			payload["ev_data"]={}
			payload["ev_data"]["ckey"]=self.ckey
			payload["ceid"]=self.ceid
			self.ceid+=1
			self.ws.send("4"+json.dumps(payload))
			self.istalk=False
	def on_message(self, ws, message):
		type=int(message[0])
		if type==3: return
		data=json.loads(message[1:])
		#print(type, data)
		if type==0:
			self.sid=data["sid"]
			self.pingInterval=data["pingInterval"]
			self.pingTimeout=data["pingTimeout"]
			Timer(self.pingInterval/1000, self.ping).start()
		elif type==4:
			if "ev_name" in data:
				if data["ev_name"]=="cn_acc":
					ev_data=data["ev_data"]
					self.conn_id=ev_data["conn_id"]
					self.hash=ev_data["hash"]
					self.tlce=ev_data["tlce"]
					payload={}
					payload["ev_name"]="_cinfo"
					payload["ev_data"]={}
					payload["ev_data"]["hash"]=self.hash
					payload["ev_data"]["dpa"]=True
					payload["ev_data"]["caper"]=True
					self.ws.send("4"+json.dumps(payload))
					self.startSearch()
				elif data["ev_name"]=="caprecvsas" or data["ev_name"]=="capchresp":
					print("SOLVING CAPTCHA...", flush=True)
					self.captchaTries=0
					self.captcha_file="captchas/captcha.jpg"
					with open(self.captcha_file, "wb") as captchafile:
						captchafile.write(base64.b64decode(data["ev_data"]["tlce"]["data"][22:]))
					self.solve_captcha()
				elif data["ev_name"]=="capissol":
					solver.report(self.captchaId, data["ev_data"]["success"])
					if data["ev_data"]["success"]:
						self.captchaTries=0
						os.rename(self.captcha_file, "captchas/"+self.captchaCode+".jpg")
						self.startSearch()
						print("STARTED SEARCH", flush=True)
					else:
						print("CAPTCHA FAIL", flush=True)
						if self.captchaTries<3:
							self.solve_captcha()
						else:
							print("REQUESTED NEW CAPTCHA", flush=True)
							self.ws.send('4{"ev_name":"_capch"}')
							self.captchaTries=0
				elif data["ev_name"]=="talk_s":
					print("NEW CONVERSATION:", flush=True)
					self.idn=0
					self.ckey=data["ev_data"]["ckey"]
					payload={}
					payload["ev_name"]="_begacked"
					payload["ev_data"]={}
					payload["ev_data"]["ckey"]=self.ckey
					payload["ceid"]=self.ceid
					self.ceid+=1
					self.ws.send("4"+json.dumps(payload))
					self.istalk=True
					self.setTyping(False)
					self.sendMessage("km")
					self.logfile="logs/"+date()+".txt"
					while not self.msgqueue.empty():
						self.sendMessage(self.msgqueue.get())
				elif data["ev_name"]=="sdis":
					print("Disconnected.", flush=True)
					self.startSearch()
				elif data["ev_name"]=="count":
					pass
				elif data["ev_name"]=="styp":
					if data["ev_data"]: print("TYPING")
					else: print("NOT TYPING")
				elif data["ev_name"]=="rmsg":
					msg=data["ev_data"]["msg"]
					print("<", msg, flush=True)
					with open(self.logfile, "a+") as f:
						f.write("< "+msg+"\n")
					if self.idn==1:
						if len(msg)<5 and 'km' not in msg.lower() and 'm' in msg.lower():
							print("SKIPPING M", flush=True)
							os.remove(self.logfile)
							self.endTalk()
						else:
							if 'km' not in msg.lower() and 'k'==msg.lower()[0]:
								beepy.beep(sound="coin")
							self.setTyping(True)
							self.sendMessage(INITIAL_MESSAGE)
					else:
						self.setTyping(True)
				elif data["ev_name"]=="convended":
					print("CONVERSATION ENDED", flush=True)
				elif data["ev_name"]=="r_svmsg":
					pass
				else:
					print("UNKEVENT", data, flush=True)
			else:
				print("UNKTYPE", type, flush=True)
	def __init__(self, host):
		self.host=host
		self.idn=0
		self.ws=websocket.WebSocketApp(host, on_message=self.on_message)
		Thread(target=self.ws.run_forever).start()

#websocket.enableTrace(True)
client=Client("wss://server.6obcy.pl:7007/6eio/?EIO=3&transport=websocket")
while True:
	i=input("> ")
	if i==":q": client.endTalk()
	else: client.sendMessage(i)
