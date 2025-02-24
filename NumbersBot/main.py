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
            self.bot.send_message(message.chat.id, "<b>Пришли мне номер спамера в формате</b>\n\n<i>+7XXXXXXXXXX - КТО_ТАКОЙ</i>\nИ я его добавлю в базу".format(message.from_user), parse_mode='html')
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
            
        @self.bot.message_handler(func=lambda message: True)
        def handle_message(message):
        # Проверка формата "номер телефона - имя"
            pattern = r"^(\+?\d{10,15})\s*-\s*(.+)$" 
            match = re.match(pattern, message.text)

            if match:
                phone = match.group(1)  
                name = match.group(2)   
                self.addRecord(phone, name, message.chat.id)  
                self.bot.reply_to(message, f"Запись добавлена\n{phone} - {name}")
            else:
                self.bot.reply_to(message, "Неверный формат записи. Правильная форма телефон - номер")
            

            
    def createUser(self, username, tg_id):
        dbO.addUser(str(username), str(tg_id))
        
    def addRecord(self, phone, name, tg_id):
        dbO.addNumber(str(phone), str(name), str(tg_id))
        
        
            









if __name__ == "__main__":
    TOKEN = "1933129297:AAFtgv9LaOgDbT6fUKnIbd1rBsVCrIA_k2o"
    logging.basicConfig(level=logging.INFO)
    dbO = DBObject("base.db")
    
    bot_instance = BotInstance(TOKEN)
    bot_instance.commands()
    bot_instance.run()