#!/usr/bin/env python
# coding: utf-8

import sys
import os
import json
import random
import multiprocessing
from time import sleep
import telegram
from telegram import Updater

TOKEN = "place your telegram token here"
INTRODUCTION = "《生命线：静夜》是一个情节深入，令人身临其境的生存类故事游戏。白星号飞船和船上的无畏船员们需要您的帮助与救援。泰勒的命运，以及这个世界的命运，就掌握在您的手里！"
LANGUAGES = {"English":"en", "Deutsch":"de", "Français":"fr", "Русский":"ru", "日本語":"jp", "中文":"cn"}

STRINGS = {}
SCENES = {}
CHOICES = {}
for lang in LANGUAGES.values():
	string_file = 'Data/strings_' + lang + '.json'
	scene_file = 'Data/waypoints_' + lang + '.json'
	choice_file = 'Data/categories_' + lang + '.json'
	with open(string_file,'r') as f:
		j = json.load(f)
		for s in j: j[s] = j[s].encode('utf-8')
		STRINGS[lang] = j

	with open(scene_file,'r') as f:
		SCENES[lang] = json.load(f)

	with open(choice_file,'r') as f:
		CHOICES[lang] = json.load(f)

# ====================================================================
class Story(object):
	def __init__(self, id, user):
		self.id = str(id)
		self.user = user
		self.status_file = 'Chat/' + self.id + '_' + self.user + '.json'
		self.status = {}
		self.lang = ''
		self.isStarted = False
		self.fastMode = False
		self.isDelaying = False
		self.bot = None
		self.update = None
		self.talkQueue = []
		self.loadStatusData()

	def loadStatusData(self):
		if os.path.exists(self.status_file):
			with open(self.status_file,'r') as f:
				self.status = json.load(f)
		else:
			self.status = {
				'Settings': {
					'lang': 'en',
					'fastMode': False,
					'atScene': 'Start',
					'isStarted': False,
					'category': 0
				}
			}

		self.lang = self.status['Settings']['lang']
		self.isStarted = self.status['Settings']['isStarted']
		self.fastMode = self.status['Settings']['fastMode']

	def saveStatusData(self, scene='Start'):
		self.status['Settings']['atScene'] = scene
		with open(self.status_file,'w') as f:
			json.dump(self.status, f)

	def handleJump(self, line):
		line = line[2:-2]
		if line[:5] == 'delay':
			tmp = []
			[delay, line] = line.split('|')
			if len(delay.split('^')) == 2:
				[delay, msg] = delay.split('^')
				tmp.append('*['+msg+']*')
			delay_time = delay.replace('delay ','').replace('s','').replace('m','*60').replace('h','*3600')
			if not self.fastMode:
				delay_time = eval(delay_time)
				tmp.append(delay_time)
			self.talkQueue.append(tmp)
		elif line[:7] == 'either(':
			talks = eval(line.replace('either',''))
			line = random.choice(talks)
		elif ']] | [[' in line:
			a, b = line.index('|'), line.index(']')
			line = line[a+1:b]
		self.status['Settings']['atScene'] = line

	def handleSet(self, line):
		line = line[7:-2].replace(' ','').split('=')
		self.status[line[0]] = line[1]

	def handleTalk(self, line):
		strings = STRINGS[self.lang]
		people = ['shep','don','bos','aries','doc','mari','green']
		line = line.replace('<i>',' _').replace('</i>','_ ')
		for tag in people:
			line = line.replace('<'+tag+'>','*'+strings['<'+tag+'>']+'*').replace('</'+tag+'>','')
		self.talkQueue.append([line])

	def handleChoice(self, line, scene):
		i = int(line[19:-2])
		self.status['Settings']['category'] = i
		choice = CHOICES[self.lang][i]["actions"]
		ques = self.talkQueue.pop()
		self.talkQueue.append([ques[0], choice[0]['short'], choice[1]['short']])
		self.saveStatusData(None)

	def atScene(self, scene):
		self.status['Settings']['atScene'] = None
		if_else = False
		skip_line = False
		self.talkQueue = []

		for line in SCENES[self.lang][scene]:
			line = line.encode('utf-8')

			if if_else:
				if line[:6] == '<<else':
					skip_line = not skip_line
					continue
				elif line == '<<endif>>':
					if_else = False
					continue

				if skip_line: continue

			if line[:4] == '<<if':
				if_else = True
				if_line = line[5:-2].replace('&&','and').replace('||','or').replace('false','\'false\'').replace('true','\'true\'')
				if_line = if_line.replace(' is','\'] ==').replace('gte','>=').replace('$','self.status[\'')

				if 'visited()' in if_line:
					key = scene+'_visited'
					if key in self.status:
						self.status[key] += 1
					else: self.status[key] = 1
					if_line = if_line.replace('visited()',str(self.status[key]))

				if '=' not in if_line:
					if_line += '\'] == \'true\''

				skip_line = False if eval(if_line) else True
			elif line[:5] == '<<set': self.handleSet(line)
			elif line[:2] == '[[': self.handleJump(line)
			elif line[:10] == '<<category': self.handleChoice(line, scene)
			else: self.handleTalk(line)

		self.sendQueue()

	def start(self):
		while self.status['Settings']['atScene'] is not None:
			if self.isDelaying: break
			self.atScene(self.status['Settings']['atScene'])

	def sendQueue(self):
		for line in self.talkQueue:
			if len(line) == 1:
				self.sendMarkdown(line[0])
			elif len(line) == 2:
				# send delay
				self.sendMarkdown(line[0])
				self.isDelaying = True
				p = multiprocessing.Process(target=self.delay, args=(line[1],))
				p.start()
			elif len(line) == 3:
				self.sendChoice(*line)
		self.talkQueue = []

	def delay(self, t):
		sleep(t)
		self.isDelaying = False
		self.start()

	def waitForAns(self, reply):
		i = self.status['Settings']['category']
		choice = CHOICES[self.lang][i]["actions"]
		if reply == choice[0]['short'].encode('utf-8'):
			self.status['Settings']['atScene'] = choice[0]['identifier']
		elif reply == choice[1]['short'].encode('utf-8'):
			self.status['Settings']['atScene'] = choice[1]['identifier']

		self.start()

	def sendMarkdown(self, text):
		# text = "*bold* _italic_ [link](http://google.com)."
		self.bot.sendChatAction(chat_id=self.update.message.chat_id, action=telegram.ChatAction.TYPING)
		reply_markup = telegram.ReplyKeyboardHide()
		self.bot.sendMessage(chat_id=self.update.message.chat_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=reply_markup)

	def sendChoice(self, ques, choice1, choice2):
		custom_keyboard = [[ choice1 ], [ choice2 ]]
		reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
		self.bot.sendMessage(chat_id=self.update.message.chat_id, text=ques, parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=reply_markup)

# ====================================================================
def start(bot, update):
	chat_id = update.message.chat_id
	user = update.message.from_user.username
	file = 'Chat/'+str(chat_id)+'_'+user+'.json'

	if os.path.exists(file): os.remove(file)

	bot.sendMessage(chat_id=chat_id, text=INTRODUCTION)
	sendTypingAction(bot, update)
	setLang(bot, update)

def sendTypingAction(bot, update):
	bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)

def help(bot, update):
	text = "[*] Help\nThis is a game bot.\nI cant give you a help." + telegram.Emoji.PILE_OF_POO
	bot.sendMessage(chat_id=update.message.chat_id, text=text)

def sendMarkdown(bot, update):
	bot.sendMessage(chat_id=update.message.chat_id, text="*bold* _italic_ [link](http://google.com).", parse_mode=telegram.ParseMode.MARKDOWN)

def setLang(bot, update):
	custom_keyboard = [[ "English", "Deutsch", "Français"], ["Русский", "日本語", "中文" ]]
	reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
	bot.sendMessage(chat_id=update.message.chat_id, text="Language:", reply_markup=reply_markup)

def setAppleWatch(bot, update, lang):
	custom_keyboard = [[ STRINGS[lang]['dialog_notification_option_1'] ], [ STRINGS[lang]['dialog_notification_option_2'] ]]
	reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
	bot.sendMessage(chat_id=update.message.chat_id, text=STRINGS[lang]['dialog_notification_settings'], reply_markup=reply_markup)

def setFastMode(bot, update, lang):
	custom_keyboard = [[ STRINGS[lang]['dialog_yes'] , STRINGS[lang]['dialog_no'] ]]
	reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
	bot.sendMessage(chat_id=update.message.chat_id, text=STRINGS[lang]['dialog_fast_confirmation'], reply_markup=reply_markup)

def sendCommunication(bot, update, lang):
	reply_markup = telegram.ReplyKeyboardHide()
	text = STRINGS[lang]['story_incoming_communication']
	bot.sendMessage(chat_id=update.message.chat_id, text=text, reply_markup=reply_markup)

def unknown(bot, update):
	text = "作者: Urinx\n欢迎关注我的微信公众号：[Urinx](http://weixin.sogou.com/gzh?openid=oIWsFt6BhfHwKUIyFvNp6A6JEsGM&ext=SvSD3-ubD_vCXrFwpUI5TIZ43Ytav-wlG8G0bt8fByo7_nWg-1AmpgMNU5FouX0x)"
	bot.sendMessage(chat_id=update.message.chat_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN)
	bot.sendPhoto(chat_id=update.message.chat_id, photo='http://chuantu.biz/t2/22/1450352449x-1376436579.jpg')

def main(bot, update):
	reply = update.message.text.encode("utf-8")
	user = update.message.from_user.username
	chat_id = update.message.chat_id
	story = Story(chat_id, user)
	story.bot = bot
	story.update = update
	lang = story.lang
	if not story.isStarted:
		# Language reply
		if reply in LANGUAGES:
			lang = LANGUAGES[reply]
			setAppleWatch(bot, update, lang)
			story.status['Settings']['lang'] = lang
			story.saveStatusData()
			return
		# Apple Watch reply
		elif reply in [STRINGS[lang]['dialog_notification_option_1'],STRINGS[lang]['dialog_notification_option_2']]:
			setFastMode(bot, update, lang)
			return
		# Fast Mode reply
		elif reply in [STRINGS[lang]['dialog_yes'],STRINGS[lang]['dialog_no']]:
			sendTypingAction(bot, update)
			sendCommunication(bot, update, lang)
			sendTypingAction(bot, update)
			story.status['Settings']['fastMode'] = True if reply == STRINGS[lang]['dialog_yes'] else False
			story.status['Settings']['isStarted'] = True
			story.saveStatusData()
			sleep(1)
			story.start()
			return
	else:
		story.waitForAns(reply)

if __name__ == '__main__':
	updater = Updater(token=TOKEN)
	dispatcher = updater.dispatcher

	dispatcher.addTelegramCommandHandler('start', start)
	dispatcher.addTelegramCommandHandler('help', help)
	dispatcher.addTelegramMessageHandler(main)
	dispatcher.addUnknownTelegramCommandHandler(unknown)

	updater.start_polling()