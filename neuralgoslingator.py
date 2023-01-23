from typing import Union
import telebot
import config
import random
import time
from telebot import types
import random
import markovify
from multiprocessing import *

joinedFile = open("users", "r")
joinedUsers = set ()
for line in joinedFile:
        joinedUsers.add(line.strip())
joinedFile.close()

with open("compl.txt",encoding='utf-8') as f:
    text = f.read()
text_model = markovify.Text(text)

#with open('mark.txt') as f:
    #my_list = [x.strip() for x in f]
        
bot = telebot.TeleBot("TOKENAPI")

#start command
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, text_model.make_sentence())

    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add(*[types.KeyboardButton(name) for name in['Гослинг, дай мне мудрость']])
    keyboard.add(*[types.KeyboardButton(name) for name in['О боте']])
    bot.send_message(message.chat.id, '↓ выбери дальнейшее действие ↓', reply_markup=keyboard, parse_mode="Html")

    if not str(message.chat.id) in joinedUsers:
        joinedFile = open('users', 'a')
        joinedFile.write("{imia}\n".format(imia=message.chat.id))
        joinedUsers.add(message.chat.id)

#commands for keyboard
@bot.message_handler(content_types=['text'])
def inl(message):
    if message.chat.type == 'private':
        if message.text == "Гослинг, дай мне мудрость":
            #bot.send_message(message.chat.id, random.choice(my_list));
            bot.send_message(message.chat.id, text_model.make_sentence())
        elif message.text == "О боте":
            bot.send_message(message.chat.id, "Бот работает на цепях Маркова и генерирует случайную фразу из военного устава, отзывов и цитат из пабликов.\nСайт автора: https://vakarian.website\nGitHub: https://github.com/vakarianplay")
            bot.send_message(message.chat.id, 'Смотрите также:\n@youarefagotbot - бот напомнит кто ты по жизни\n@batushkin - нейроправославный канал')
        else:
            bot.send_message(message.chat.id, 'Дон`т андерстенд')




# bot.polling
if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True) #start bot
        except:
            time.sleep(10)
