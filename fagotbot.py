from typing import Union
import telebot
import config
import random
import schedule
import time
from telebot import types
import random
from multiprocessing import *

#pics for send
foo = ['https://sun9-39.userapi.com/oW_Pcfu4zAfQquuJDLXmReHhE7d_SsT5vzOWZA/-QDuxdEPJ54.jpg', 'https://sun9-31.userapi.com/YplfFCyTJb7ILAd0W-nGq8RlVwx5GYyscRyDcg/E1k5d8P_Xpg.jpg', 'https://sun9-26.userapi.com/N6cUOLmFegIq-RWPdMZnePfwO1CcPlL6qUUKjg/EiTCrhwGXyU.jpg', 'https://sun9-61.userapi.com/H3GLPSAvpuS0Umhx1IhF1VMYYnPmXCr_Rmm1tg/wDlCisnAEk0.jpg', 'https://sun9-33.userapi.com/lH_-Dzs1oW5lELSrcz2uTK1foweqqlYhu9y2EA/9FMC87LoduQ.jpg', 'https://sun9-59.userapi.com/2-As9DYGwWB3g9oh_rAGebvxWf4vd8JpDtMGJQ/L-LHOSW_xYE.jpg', 'https://sun9-69.userapi.com/jt2Q5BPu7OyUaEwMNxx5MsOQ3MFMdaP5y6iRoQ/HPKvIQn9bac.jpg', 'https://sun9-49.userapi.com/d30e75FrBpGD4wTJpvbIOzyudKwf9S8uPVuC7Q/ft2BxaqBFnc.jpg']

#open base of users id and create set
joinedFile = open("join", "r")
joinedUsers = set ()
for line in joinedFile:
        joinedUsers.add(line.strip())
joinedFile.close()

#start schedule process
def start_process():
    p1 = Process(target=P_schedule.start_schedule, args=()).start()

# Class for schedule
class P_schedule():
    def start_schedule():
        #schedule settings
        schedule.every().day.at("11:02").do(P_schedule.send_message1)
        schedule.every().day.at("15:31").do(P_schedule.send_message2)

        while True:
            schedule.run_pending()
            time.sleep(1)

    #scheduled messages
    def send_message1():
        for user in joinedUsers:
            try:
                bot.send_message(user, "Ты пидорас!\n@youarefagotbot всегда тебе напомнит кто ты.")
            except:
                pass


    def send_message2():
        for user in joinedUsers:
            try:
                bot.send_photo(user, random.choice(foo));
            except:
                pass



bot = telebot.TeleBot("TOKEN")


#start command
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, 'ТЫ ПИДОРАС')
    #sending random pic from foo
    bot.send_photo(message.chat.id, random.choice(foo));
    # keyboard
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("КТО Я?")
    item2 = types.KeyboardButton("ТЫ ПИДОРАС!")

    markup.add(item1, item2)

    #record id in base
    if not str(message.chat.id) in joinedUsers:
        joinedFile = open('join', 'a')
        joinedFile.write("{imia}\n".format(imia=message.chat.id))
        joinedUsers.add(message.chat.id)


    bot.send_message(message.chat.id,
                     "Ты пидорас, {0.first_name}!\n<b>{1.first_name}</b> всегда напомнит тебе кто ты.".format(
                         message.from_user, bot.get_me()),
                     parse_mode='html', reply_markup=markup)

#commands for keyboard
@bot.message_handler(content_types=['text'])
def inl(message):
    if message.chat.type == 'private':
        if message.text == "КТО Я?":
            bot.send_photo(message.chat.id, random.choice(foo));
            bot.send_message(message.chat.id, "Ты пидорас, {0.first_name}!\n<b>{1.first_name}bot</b> всегда напомнит тебе кто ты.".format(message.from_user, bot.get_me()), parse_mode='html')
        elif message.text == "ТЫ ПИДОРАС!":
            bot.send_message(message.chat.id, "ТЫ ПИДОРАС\n YOU ARE FAGOT\n ТИ ПИДОРАСiВ\n BIST DU HOMOSEXUELL\n ÊTES-VOUS GAY\n СЕН ГЕЙСІҢ БЕ\n ԴՈՒ ՀԱՄԱՍԵՌԱՄՈԼ ԵՍ\n 당신은 게이입니까\n あなたは同性愛者ですか")
        else:
            bot.send_message(message.chat.id, 'Иди нахуй, пидорас.')




# RUN
if __name__ == '__main__':
    start_process()
    try:
        bot.polling(none_stop=True)
    except:
        time.sleep(10)
