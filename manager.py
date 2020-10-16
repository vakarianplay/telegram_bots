import telebot
import os

#set token for bot
token = "Token"
bot = telebot.TeleBot(token)

#start command
@bot.message_handler(commands=['start'])
def privetctive(message):
    sent = bot.send_message(message.chat.id, "Hello, what's you name?")
    #rec answer to var
    bot.register_next_step_handler(sent, Hello)


def Hello(message):
    bot.send_message(message.chat.id, 'Hello, {name}. What are you speciality?'. format(name=message.text))
    #open and write to file user's answers
    doc = open('file.txt', 'w')
    doc.write("Name of customer - {imia}\n".format(imia=message.text))

#text command
@bot.message_handler(content_types=['text'])
def repeat_all_messages(message):
    #create reply keyboard
    user_markup = telebot.types.ReplyKeyboardMarkup(True)
    #menu
    user_markup.row('Test1', 'Test2')
    user_markup.row('Test3', 'Test4')
    user_markup.row('Test5')
    #new question
    uslugi = bot.send_message(message.from_user.id, "What services do you
interested?", reply_markup=user_markup)
    #reg new date
    bot.register_next_step_handler(uslugi, telephon)
    #open file and add new answers
    doc = open('file.txt', 'a')
    doc.write("What is your working? - {zanatie}\n".format(zanatie=message.text))


def telephon(message):
    #new question
    nomer = bot.send_message(message.chat.id, 'Please leave us your contact number')
    #reg new date
    bot.register_next_step_handler(nomer, poka)
    #open file and add new answers
    doc = open('file.txt', 'a')
    doc.write("Service - {uslugi}\n".format(uslugi=message.text))


def poka(message):
    bot.send_message(message.chat.id, "Thank for your attention. We will contact you soon.")
    doc = open('file.txt', 'a')
    doc.write("Phone - {telephon}\n".format(telephon=message.text))
    doc.close()
    file_to_send = open('file.txt', 'rb')
    bot.send_document(000000000, file_to_send)
    file_to_send.close()
    os.remove('file.txt')

#pool bot via api
if __name__ == '__main__':
     bot.polling()
