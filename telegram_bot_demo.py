#!/usr/bin/env python

import telegram
from telegram import Updater

updater = Updater(token='')
dispatcher = updater.dispatcher

def start(bot, update):
	bot.sendMessage(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")

def echo(bot, update):
	bot.sendMessage(chat_id=update.message.chat_id, text=update.message.text)

def markdown(bot, update):
	bot.sendMessage(chat_id=update.message.chat_id, text="*bold* _italic_ [link](http://google.com).", parse_mode=telegram.ParseMode.MARKDOWN)

def Emoji(bot, update):
	bot.sendMessage(chat_id=update.message.chat_id, text=telegram.Emoji.PILE_OF_POO)

def image(bot, update):
	bot.sendPhoto(chat_id=update.message.chat_id, photo='https://telegram.org/img/t_logo.png')

def voice(bot, update):
	bot.sendVoice(chat_id=update.message.chat_id, voice=open('asserts/telegram.ogg','rb'))

def action(bot, update):
	bot.sendChatAction(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)

def createCustomKeyboards(bot, update):
	custom_keyboard = [[ telegram.Emoji.THUMBS_UP_SIGN, telegram.Emoji.THUMBS_DOWN_SIGN ]]
	reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
	bot.sendMessage(chat_id=update.message.chat_id, text="Stay here, I'll be back.", reply_markup=reply_markup)

def hideCustomKeyboards(bot, update):
	reply_markup = telegram.ReplyKeyboardHide()
	bot.sendMessage(chat_id=update.message.chat_id, text="I'm back.", reply_markup=reply_markup)

def unknown(bot, update):
	bot.sendMessage(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")

def caps(bot, update, args):
	text_caps = ' '.join(args).upper()
	bot.sendMessage(chat_id=update.message.chat_id, text=text_caps)

def help(bot, update):
	bot.sendMessage(chat_id=update.message.chat_id, text="/caps\n/markdown\n/Emoji\n/image\n/voice\n/action\n/keyboard\n/hide\n/help")

dispatcher.addTelegramCommandHandler('start', start)
dispatcher.addTelegramCommandHandler('caps', caps)
dispatcher.addTelegramCommandHandler('markdown', markdown)
dispatcher.addTelegramCommandHandler('Emoji', Emoji)
dispatcher.addTelegramCommandHandler('image', image)
dispatcher.addTelegramCommandHandler('voice', voice)
dispatcher.addTelegramCommandHandler('action', action)
dispatcher.addTelegramCommandHandler('keyboard', createCustomKeyboards)
dispatcher.addTelegramCommandHandler('hide', hideCustomKeyboards)
dispatcher.addTelegramCommandHandler('help', help)
dispatcher.addTelegramMessageHandler(echo)
dispatcher.addUnknownTelegramCommandHandler(unknown)

updater.start_polling()
# updater.stop()
