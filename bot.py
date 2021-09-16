from subprocess import check_output
import telebot
from telebot import types
import time

#bot token
bot = telebot.TeleBot("TOKEN")
#id of your account
user_id = ID
@bot.message_handler(content_types=["text"])
def main(message):
   #check id
	if (user_id == message.chat.id):
		comand = message.text
		#markup keyboard
		keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
		keyboard.row('sensors', 'uptime', 'free -h', 'ls')
		keyboard.row('mpc', 'mpc next')
		keyboard.row('curl wttr.in/?0T')
		
      #if no command - check_output exception
		try: 
			bot.send_message(message.chat.id, check_output(comand, shell = True), reply_markup=keyboard)
		except:
         #incorrect command
			bot.send_message(message.chat.id, "Invalid input", reply_markup=keyboard) 
         
#bot.polling         
if __name__ == '__main__':
    while True:
        try: 
            bot.polling(none_stop=True) #start bot
        except:
            time.sleep(10)
			
			
			