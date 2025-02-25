import telebot
import logging
from sqlprocessor import DBObject
import re

class BotInstance:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token)

        
    def run(self):
        logging.info("Bot started!")
        self.bot.polling(none_stop=True)

    def commands(self):
        @self.bot.message_handler(commands=['start'])
        def handleStart(message):
            self.bot.send_message(message.chat.id, "<b>Пришли мне номер спамера в формате</b>\n\n<i>+7XXXXXXXXXX - КТО_ТАКОЙ</i>\nИ я его добавлю в базу\n\n <i>/help - показать справку</i>".format(message.from_user), parse_mode='html')
            self.createUser(message.chat.username, message.chat.id)
            
        @self.bot.message_handler(commands=['getrecords'])
        def sendRecords(message):
            records = dbO.getRecords()

            if not records:
                self.bot.reply_to(message, "БД пустая.")
                return

            file_path = "records.txt"

            with open(file_path, "w", encoding="utf-8") as file:
                for phone, caption in records:
                    file.write(f"{phone} - {caption}\n")

            with open(file_path, "rb") as file:
                self.bot.send_document(message.chat.id, file, caption="Выгрузка БД")
                
        @self.bot.message_handler(commands=['countrecors'])
        def countRecords(message):
            self.bot.reply_to(message, "Количество записей в БД\n<b>" + str(dbO.countRecords())+ "</b>", parse_mode='html')
            
        @self.bot.message_handler(commands=['help'])
        def handleHelp(message):
            firstLine = "/help - эта справка\n\n/getrecords - получить содержимое базы в txt файле\n\n"
            secondLine = "/countrecors - количество записей в базе"
            self.bot.send_message(message.chat.id, firstLine + secondLine, parse_mode='html')
            
        @self.bot.message_handler(func=lambda message: True)
        def handle_message(message):
            pattern = r"^(\+?\d{10,15})\s*-\s*(.+)$" 
            match = re.match(pattern, message.text)

            if match:
                phone = match.group(1)  
                name = match.group(2)   
                if not self.addRecord(phone, name, message.chat.id):
                    self.bot.reply_to(message, f"Запись добавлена\n{phone} - {name}")
                else:
                    self.bot.reply_to(message,f"Запись с номером {phone} уже существует")
            else:
                self.bot.reply_to(message, "Неверный формат записи. Правильная форма телефон - номер")
            

    def createUser(self, username, tg_id):
        dbO.addUser(str(username), str(tg_id))
        
    def addRecord(self, phone, name, tg_id):
        addResult = dbO.addNumber(str(phone), str(name), str(tg_id))
        return  addResult
        
        
if __name__ == "__main__":
    TOKEN = "TOKEN_API"
    logging.basicConfig(level=logging.INFO)
    dbO = DBObject("base.db")
    
    bot_instance = BotInstance(TOKEN)
    bot_instance.commands()
    bot_instance.run()
