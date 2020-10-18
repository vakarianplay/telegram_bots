from subprocess import check_output
import telebot
import time

bot = telebot.TeleBot("BOT_API") #tokenapi
user_id = 0 #id
@bot.message_handler(content_types=["text"])
def main(message):
   if (user_id == message.chat.id): #check id
      comand = message.text  
      try: #if no command - check_output exception
         bot.send_message(message.chat.id, check_output(comand, shell = True))
      except:
         bot.send_message(message.chat.id, "Invalid input") #incorrect
if __name__ == '__main__':
    while True:
        try: 
            bot.polling(none_stop=True) #start bot
        except:
            time.sleep(10)
