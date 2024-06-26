import telebot
import csv
import logging
import random
import time

class UsersList:
    def __init__(self, filename='/home/glab/LCLbot/users.csv'):
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

class BotProps:
    toxic_dict = {
    'комфортик дохуя': range(0, 45),
    'токсик ебаный': range(46, 95),
    'пиздец токсик, так еще и душнила': range(96, 146)
    }
    
    def __init__(self) -> None:
        pass
        
    def fightAssets(self):
        fights = ["СЛАВЯНСКИЙ ЗАЖИМ ЯЙЦАМИ", "СЛАВЯНСКИЙ ЗАЖИМ ЛЯЖКАМИ", "расстрел ЧВК Творожок", "газовую атаку подмыхой", "прострел сундука", 
                  "травматический ЯДЕРНЫЙ бабах", "добивание выживших", "НЕБЕСНЫЙ КАМШОТ", "АТАКУ ДРОЧЕСЛАВА", "установку на понос", "СЛАВЯНСКИЙ УДАР ЗАЛУПОЙ", 
                  "АТАКУ ПОДНЕБЕСНОГО", "инцелшот", "слонярскую базу"]
        return random.choice(fights)
    
    def boobsSize(self):
        sizes = ["нулевого", "первого", "второго", "третьего", "четвертого"]
        return random.choice(sizes)
    
    def ballsMass(self):
        mass = random.randint(50, 1488)
        return str(mass) + " грамм"
    
    def toxicLvl(self, username):
        lvl = random.randint(15, 146)
        # statusToxic = self.getStatusToxic(lvl)
        return "<b>Уровень токсичности <u>" + str(lvl) + " %</u></b>\n\n" + username + " ты <i>" + self.getToxicStatus(lvl) + "</i>"
    
    def getToxicStatus(self, toxicLvl):
        for level, range in self.toxic_dict.items():
            if toxicLvl in range:
                return level
    
    def fixUsername(self, message):
        if message.from_user.username == None:
            username = message.from_user.first_name
        else:
            username = message.from_user.username
        return username
    
    def pingProcessor(self):
        start_time = time.time()
        curTime = time.strftime('%H:%M:%S', time.localtime())
        end_time = time.time()
        execTime = end_time - start_time
        
        return f'Бот онлайн!\nВремя на сервере: {curTime}\nВремя выполнения: {execTime} с'
        

class LCLBot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token)
        self.users_list = UsersList()
        self.props = BotProps()

    def commands(self):
        @self.bot.message_handler(commands=['start'])
        def handleStart(message):
            self.bot.send_message(message.chat.id, "<b>Ты пидорас, {0.first_name}!</b>\n\n<i>@youarefagotbot</i> всегда напомнит тебе кто ты.".format(message.from_user), parse_mode='html')
            self.users_list.addUser(message.chat.id, message.chat.username)

        @self.bot.message_handler(commands=['help'])
        def handleStart(message):
            firstLine = "/help - эта справка\n\n/whoami - узнать кто я\n\n"
            secondLine = "/whois @username - узнать кто такой @username (вводить через проблел)\n\n/fight @username - устроить бой с @username (вводить через пробел)\n\n"
            thirdLine = "/toxic - Узнать уровень токсичности @username\n\n/boobsmetr - узнать размер бубсов\n\n/ballsmetr - узнать массу яиц"
            self.bot.send_message(message.chat.id, firstLine + secondLine + thirdLine, parse_mode='html')
            
        @self.bot.message_handler(commands=['ping'])
        def handleMsg(message):
            logging.info("Ping command")
            self.bot.reply_to(message, f"<b>PONG!</b>", parse_mode='html')
            self.bot.reply_to(message, self.props.pingProcessor(), parse_mode='html')
            

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
                self.bot.reply_to(message, "Ты долбоеб!\nПравильная команда выглядит так \n/whois @username\nЗапоминай!")

        @self.bot.message_handler(commands=['fight'])
        def fight(message):
            logging.info("Fight command")
            if len(message.text.split()) == 2:
                sender_username = self.props.fixUsername(message)
                
                opponent_username = message.text.split()[1][0:]
                opponent_username_split = message.text.split()[1][1:]
                
                if opponent_username_split == sender_username:
                    self.bot.reply_to(message, "ТЫ ЧЕ, ДОЛБОЕБ?\nНахуй ты так делаешь?")
                else: 
                    winner = random.choice([sender_username, opponent_username])
                    punch = self.props.fightAssets()
                    self.bot.send_message(message.chat.id, f"🥊 <b>БОЙ МЕЖДУ</b> 🥊\n🥊 <i>@{sender_username} и {opponent_username}</i> 🥊", parse_mode='html')
                    self.bot.send_message(message.chat.id, f"{winner} применил \n\n<b><u>{punch}</u></b>\n\n\n🏆 <b>ПОБЕДА!</b> 🏆", parse_mode='html')
            else:
                self.bot.reply_to(message, "Ты долбоеб!\nПравильная команда выглядит так \n/fight @username\nЗапоминай!")

        @self.bot.message_handler(commands=['boobsmetr'])
        def handleMsg(message):
            logging.info("Boobs command") 
            self.bot.reply_to(message, f"<b>{message.from_user.first_name}</b>, твои бубсы <u>{self.props.boobsSize()} размера!</u>", parse_mode='html')

        @self.bot.message_handler(commands=['ballsmetr'])
        def handleMsg(message):
            logging.info("Balls command")
            self.bot.reply_to(message, f"<b>{message.from_user.first_name}</b>, твои яйца весят <u>{self.props.ballsMass()}!</u>", parse_mode='html')
        
        @self.bot.message_handler(commands=['toxic'])
        def handleMsg(message):
            logging.info("Toxic command")
            if len(message.text.split()) == 2:
                username = message.text.split(' ')[1][0:]
                toxicAns = self.props.toxicLvl(username)
                self.bot.reply_to(message, toxicAns, parse_mode='html')
            else:
                self.bot.reply_to(message, "Ты долбоеб!\nПравильная команда выглядит так \n/toxic @username\nЗапоминай!")
    
    def run(self):
        logging.info("Bot started!")
        self.bot.polling(none_stop=True)

if __name__ == "__main__":
    TOKEN = "APITOKEN"
    logging.basicConfig(level=logging.INFO)

    bot_instance = LCLBot(TOKEN)
    bot_instance.commands()
    bot_instance.run()
