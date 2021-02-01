from subprocess import check_output
import telebot
import time

#tokenapi
bot = telebot.TeleBot("BOT_API") 
#telegram user if
user_id = 0 
@bot.message_handler(content_types=["text"])
def main(message):
   #check id
   if (user_id == message.chat.id):
      comand = message.text  
      #if no command - check_output exception
      try: 
         bot.send_message(message.chat.id, check_output(comand, shell = True))
      except:
         #incorrect command
         bot.send_message(message.chat.id, "Invalid input") 
         
#bot.polling         
if __name__ == '__main__':
    while True:
        try: 
            bot.polling(none_stop=True) #start bot
        except:
            time.sleep(10)
