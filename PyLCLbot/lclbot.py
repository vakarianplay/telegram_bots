import telebot
import csv
import logging
import random

class UsersList:
    def __init__(self, filename='users.csv'):
        self.filename = filename

    def isUserExists(self, user_id):
        with open(self.filename, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                if str(user_id) == row[0]:
                    return True
        return False

    def addUser(self, user_id, username):
        if not self.isUserExists(user_id):
            with open(self.filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([user_id, username])
                logging.info(f"New user joined! User id: {user_id}, Username: {username}")

class LCLBot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token)
        self.users_list = UsersList()

    def commands(self):
        @self.bot.message_handler(commands=['start'])
        def handleStart(message):
            self.bot.send_message(message.chat.id, "<b>Ты пидорас, {0.first_name}!</b>\n\n<i>@youarefagotbot</i> всегда напомнит тебе кто ты.".format(message.from_user), parse_mode='html')
            self.users_list.addUser(message.chat.id, message.chat.username)

        @self.bot.message_handler(commands=['whoami'])
        def handleMsg(message):
            logging.info("Whoami command")
            self.bot.send_message(message.chat.id, "<b>Ты пидорас, {0.first_name}!</b>".format(message.from_user), parse_mode='html')

        @self.bot.message_handler(commands=['whois'])
        def handleMsg(message):
            logging.info("Whois command")
            if len(message.text.split()) == 2:
                username = message.text.split(' ')[1][0:]
                perc = random.randint(12, 150)
                self.bot.reply_to(message, f"<b>{username}</b> пидорас на {perc}%", parse_mode='html')
            else:
                self.bot.reply_to(message, "Ты долбоеб!\nПравильная команда выглядит так /whois @username\nЗапоминай!")

        @self.bot.message_handler(commands=['fight'])
        def fight(message):
            logging.info("Fight command")
            if len(message.text.split()) == 2:
                sender_username = message.from_user.username
                opponent_username = message.text.split()[1][0:]
                opponent_username_split = message.text.split()[1][1:]
                

                if opponent_username_split == sender_username:
                    self.bot.reply_to(message, "ТЫ ЧЕ, ДОЛБОЕБ?\nНахуй ты так делаешь?")
                else: 
                    winner = random.choice([sender_username, opponent_username])
                    self.bot.send_message(message.chat.id, f"🥊 БОЙ МЕЖДУ @{sender_username} и {opponent_username} 🥊")
                    self.bot.send_message(message.chat.id, f"{winner} применил СЛАВЯНСКИЙ ЗАЖИМ ЯЙЦАМИ. ПОБЕДА! 🏆")
            else:
                self.bot.reply_to(message, "Ты долбоеб!\nПравильная команда выглядит так /fight @username\nЗапоминай!")


            
    def run(self):
        logging.info("Bot started!")
        self.bot.polling(none_stop=True)


if __name__ == "__main__":
    TOKEN = "TOKEN"
    logging.basicConfig(level=logging.INFO)

    bot_instance = LCLBot(TOKEN)
    bot_instance.commands()
    bot_instance.run()
