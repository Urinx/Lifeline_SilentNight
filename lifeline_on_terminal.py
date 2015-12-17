#!/usr/bin/env python
# coding: utf-8
import sys
import os
import json
import random
from time import sleep

def echo(str):
	sys.stdout.write(str)
	sys.stdout.flush()

class Lifeline(object):
	def __init__(self, lang='en'):
		self.lang = lang
		self.strings = None
		self.player = 'Player'
		self.fastMode = False
		self.loadString()

	def __str__(self):
		return '《生命线：静夜》是一个情节深入，令人身临其境的生存类故事游戏。白星号飞船和船上的无畏船员们需要您的帮助与救援。泰勒的命运，以及这个世界的命运，就掌握在您的手里！'

	def __repr__(self):
		return self.__str__()

	def loadString(self):
		file = 'Data/strings_' + self.lang + '.json'
		with open(file,'r') as f:
			self.strings = json.load(f)

	def setLang(self):
		print self.strings['dialog_change_language_text']
		print '1.',self.strings['dialog_change_language_en_button']
		print '2.',self.strings['dialog_change_language_de_button']
		print '3.',self.strings['dialog_change_language_fr_button']
		print '4.',self.strings['dialog_change_language_ru_button']
		print '5.',self.strings['dialog_change_language_jp_button']
		print '6.',self.strings['dialog_change_language_cn_button']
		lang = ['en','de','fr','ru','jp','cn']
		while 1:
			n = raw_input(self.player+'> ')
			if n.isdigit() and int(n) < 7 and int(n) > 0:
				self.lang = lang[int(n)-1]
				self.loadString()
				break
			else: print 'Please input a number (1-6)'

	def setPlayer(self):
		while 1:
			print '\n',self.strings['story_my_name_is']+self.strings['text_input_placeholder']+'?'
			name = raw_input(self.player+'> ')
			print '\n',self.strings['dialog_name_confirmation'],name,'(y/n)'
			ans = raw_input(self.player+'> ')
			if ans.lower() == 'y':
				self.player = name
				break

	def setAppleWatch(self):
		print '\n[*] Apple Watch'
		print self.strings['dialog_notification_settings']
		print '1.',self.strings['dialog_notification_option_1']
		print '2.',self.strings['dialog_notification_option_2']
		raw_input(self.player+'> ')

	def setFastMode(self):
		print '\n[*] Fast Mode'
		print self.strings['dialog_fast_confirmation'],'(y/n)'
		while 1:
			try:
				ans = raw_input(self.player+'> ')
			except:
				print '\n[*] Quit\n'
				exit()
			if ans in ('y', 'n'):
				self.fastMode = True if ans == 'y' else False
				break
			else:
				continue

	def saveStatusData(self, file):
		status = {
			'Settings': {
				'lang': self.lang,
				'playerName': self.player,
				'fastMode': self.fastMode,
				'atScene': 'Start'
			}
		}
		with open(file,'w') as f:
			json.dump(status,f)

	def start(self):
		status_file = 'Data/status.json'
		if not os.path.exists(status_file):
			# 初始化设置
			print '[*] Introduction\n', self,'\n'
			print '[*] Setting'
			self.setLang()
			self.setPlayer()
			self.setAppleWatch()
			self.setFastMode()
			self.saveStatusData(status_file)
		print '\033[31m' # 红色文字
		for i in range(20):
			echo('*')
			sleep(0.2)
		print '\n'
		print self.strings['story_incoming_communication'],'\033[0m\n'
		sleep(1)
		story = Story()
		story.start()

class Story(object):
	def __init__(self):
		self.status = {}
		self.scenes = {}
		self.choices = {}
		self.strings = {}
		self.lang = ''
		self.player = ''
		self.fastMode = False
		self.loadStatusData()
		self.loadStoryData()
		self.loadString()

	def loadString(self):
		file = 'Data/strings_' + self.lang + '.json'
		with open(file,'r') as f:
			self.strings = json.load(f)

	def loadStoryData(self):
		scene_file = 'Data/waypoints_'+self.lang+'.json'
		choice_file = 'Data/categories_'+self.lang+'.json'

		with open(scene_file,'r') as f:
			self.scenes = json.load(f)

		with open(choice_file,'r') as f:
			self.choices = json.load(f)

	def loadStatusData(self):
		status_file = 'Data/status.json'
		if os.path.exists(status_file):
			with open(status_file,'r') as f:
				self.status = json.load(f)
		else:
			self.status = {
				'Settings': {
					'lang': 'en',
					'playerName': 'Player',
					'fastMode': False,
					'atScene': 'Start'
				}
			}

		self.lang = self.status['Settings']['lang']
		self.player = self.status['Settings']['playerName']
		self.fastMode = self.status['Settings']['fastMode']

	def saveStatusData(self, scene):
		self.status['Settings']['atScene'] = scene
		status_file = 'Data/status.json'
		with open(status_file,'w') as f:
			json.dump(self.status, f)

	def handleJump(self, line):
		line = line[2:-2]
		if line[:5] == 'delay':
			[delay, line] = line.split('|')
			if len(delay.split('^')) == 2:
				[delay, msg] = delay.split('^')
				print '\033[33m['+msg+']\033[0m\n'
			delay_time = delay.replace('s',')').replace('m','*60)').replace('h','*3600)').replace('delay ','sleep(')
			if not self.fastMode: eval(delay_time)
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
		str = self.strings
		people = {'shep':'36','don':'36','bos':'36','aries':'35','doc':'30','mari':'35','green':'32'}
		line = line.replace('<i>','').replace('</i>','')
		for tag in people:
			line = line.replace('<'+tag+'>','\033['+people[tag]+'m'+str['<'+tag+'>']).replace('</'+tag+'>','\033[0m')
		print line,'\n'
		if not self.fastMode: sleep(2.5)

	def handleChoice(self, line, scene):
		choice = self.choices[int(line[19:-2])]["actions"]
		# 选项:黄色
		echo('\033[33m')
		print '0.',choice[0]['short']
		print '1.',choice[1]['short'],'\033[0m'
		while 1:
			try:
				i = raw_input(self.player+'> ')
			except:
				print '\n\n[*] Quit'
				print '[*] Save game data\n'
				self.saveStatusData(scene)
				exit()
			if not i:
				# i = str(random.randint(0,1)) # this is for test
				continue
			if i.isdigit() and int(i) in (0,1):
				i = int(i)
				# 我的回答:黄色
				print '\n\033[33m'+choice[i]['full']+'\033[0m\n'
				self.status['Settings']['atScene'] = choice[i]['identifier']
				break
			else:
				print 'Please input a number (0-1)'

	def atScene(self, scene):
		self.status['Settings']['atScene'] = None
		if_else = False
		skip_line = False

		for line in self.scenes[scene]:
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

	def start(self):
		while self.status['Settings']['atScene'] is not None:
			self.atScene(self.status['Settings']['atScene'])
		self.saveStatusData('Start')

if __name__ == '__main__':
	lifeline = Lifeline()
	lifeline.start()
