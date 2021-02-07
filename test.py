import telebot
import pymysql
import time
from termcolor import colored
from datetime import datetime
from pymysql.cursors import DictCursor
from contextlib import closing
from pprint import pprint

bot = telebot.TeleBot('')

def connectionDB():
    connect = pymysql.connect(
        host='',
        user='',
        password='',
        database='',
        cursorclass=DictCursor,
    )
    return connect

ag = []
with closing(connectionDB()) as connection:

    with connection.cursor() as cursor:
        query = 'SELECT number FROM general '
        cursor.execute(query)
        for row in cursor:
            ag.append(row['number'])

keyBoard1 = telebot.types.ReplyKeyboardMarkup(True,True)
keyBoard1.row('1','2')
keyBoard1.row('3','4')


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    # bot.reply_to(message, "Howdy, how are you doing?") ответить на сообщение
    bot.send_message(text=f'hello \U0001F603', chat_id=message.from_user.id )

    # print(ag)

@bot.message_handler(commands=['in'])
def get_info(message):
    message1 = message.text
    message1 = message1.split(' ')
    # print(message1)
      
    af = []
    with closing(connectionDB()) as connect:
        with connect.cursor() as cursor1:
            if len(message1)==1:

                infoQuery = 'SELECT * FROM general ORDER BY `index` DESC LIMIT 4'
                cursor1.execute(infoQuery)
                
                for row in cursor1:  
                    text = f"""
\U0000231B *{row['number']}* 
Наименование: {row['name']} 
Толщина: {row['height']}mm
Металл: {row['steel']}
Осталось: *{row['quantity']}шт*
    """            
                    bot.send_message(chat_id=message.from_user.id, text=text, parse_mode='MarkdownV2')
                return 0 

            query = 'SELECT number, name, height, steel, quantity FROM general WHERE number = %s '
            cursor1.execute(query,(message1[1]))
            for row in cursor1:
                af.append(row)
                
    text = f"""
{af[0]['number']} 
Наименование: {af[0]['name']} 
Толщина: {af[0]['height']}mm
Металл: {af[0]['steel']}
Осталось: {af[0]['quantity']}шт
    """            
    bot.send_message(chat_id=message.from_user.id, text=text)


@bot.message_handler(commands=['new'])
def create_new_user_table(message):
    with closing(connectionDB()) as connection:
        with connection.cursor() as cursor:
            createUersTable = f"""
CREATE TABLE `{message.from_user.username}` (
  `index` int(11) NOT NULL AUTO_INCREMENT,
  `number` text NOT NULL,
  `name` text NOT NULL,
  `height` int(4) NOT NULL,
  `quantity` int(5) NOT NULL,
  `steel` text NOT NULL,
  `data` date NOT NULL,
  `time` time NOT NULL,
  KEY `index` (`index`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;
"""         
            try:
                cursor.execute(createUersTable)
            except:
                bot.send_message(message.from_user.id, 'Хватит писать new хуйло \U0001F448')
            connection.commit()

@bot.message_handler(commands=['day'])
def learn_work_during_day(message):
    with closing(connectionDB()) as connect:
        with connect.cursor() as cursor:
            # query = 'SELECT * FROM general WHERE data = CURDATE()'
            query = f'SELECT number, SUM(quantity) as quantity FROM {message.from_user.username} WHERE data = CURDATE() GROUP BY number'
            cursor.execute(query)

            bot.send_message(message.from_user.id, 'За сегодня вы сделали:')   

            for row in cursor:
                text = f"""
\U0001F4AA *{row['number']}* 
Сделано: *{row['quantity']}шт*
    """   
                bot.send_message(message.from_user.id, text, parse_mode='MarkdownV2')
                


@bot.message_handler(content_types=["text"]) # Запись данных в базу
def get_data(message1): 

    try: 
        messages = split_message(message1)
    except:
        print(colored('[Fail split]','red',))

    with closing(connectionDB()) as connection:
        with connection.cursor() as cursor:
        
            userQuery = f'INSERT INTO {message1.from_user.username} (number, name, height, quantity, steel, data, time) VALUES (%s, %s, %s, %s, %s, CURDATE(), CURTIME())'
            query2 = '''SELECT number FROM general WHERE number = %s '''
            query = 'INSERT INTO general (number, name, height, quantity, steel, data) VALUES (%s, %s, %s, %s, %s, CURDATE())'
            
            try:
                cursor.execute(query2, (messages[0]))
                countRow = [] 

                for row in cursor:
                    countRow.append(row)
            except:
                bot.send_message(message1.from_user.id, 'Ошибка 401, пожалуйста обратитесь к Игорю')
                
                text1 = 'Запущена самодиагностика'
                idMessage = bot.send_message(chat_id=message1.from_user.id, text=text1).id
                # print(idMessage)

                for i in range(10):
                    text1+='.'
                    bot.edit_message_text(text1, message1.from_user.id, idMessage)
                    time.sleep(0.5)
                # time.sleep(2)
                # idMessage = bot.send_message(chat_id=message1.from_user.id, text='Запущена самодиагностика..').id
                # print(a)
                # time.sleep(2)
                bot.send_message(chat_id=message1.from_user.id, text='Возможная причина: \nНе верный формат ввода')
                bot.send_message(chat_id=message1.from_user.id, text='Пример -- 704.34.5235.12.0101 пол 2ммст3 - 21шт')
                return 0

            thereIsNumber = True if len(countRow) > 0 else False


            if thereIsNumber:
                try:
                    updateQuery = '''UPDATE general SET quantity = quantity - %s WHERE number = %s '''
                    updateUserQuery = f'INSERT {message1.from_user.username}(number, quantity, data) VALUES(%s, %s, NOW())'

                    cursor.execute(updateQuery, (messages[1], messages[0]))
                    cursor.execute(updateUserQuery, (messages[0], messages[1]))

                    connection.commit()

                    print('Обновление количества .... ', colored('[ОК]', 'green'))
                    bot.send_message(message1.from_user.id, 'Данные записаны')
                except:
                    print('Обновление количества .... ', colored('[Fail]', 'red'))
                    bot.send_message(message1.from_user.id, 'Ошибка записи 307, пожалуйста обратитесь к Игорю')

            else:
                bot.send_message(message1.from_user.id, 'Нет такой детали\nСоздана новая позиция')
                try:
                    cursor.execute(userQuery, (messages[0], messages[1],
                                        messages[2], messages[3], 
                                        messages[4], 
                                        ))
                    connection.commit()
                except:
                    return 0
                
                try: 
                    cursor.execute(query, (messages[0], messages[1],
                                        messages[2], messages[3], 
                                        messages[4], 
                                        ))
                    connection.commit()

                except:
                    bot.send_message(chat_id=message1.from_user.id, text='Не верный формат ввода')
                    bot.send_message(chat_id=message1.from_user.id, text='Пример -- 704.34.5235.12.0101 пол 2ммст3 - 21шт')
                
                
                # cursor.execute(query)



def split_message(mess):
    """[summary]

    Args:
        mess ([message]): [message]

    Returns:
        [list]: [number] --- 700.21.233.60.0101
        [list]: [name] --- Основание
        [list]: [height] --- 3mm
        [list]: [quantity] --- 21шт
        [list]: [steel] --- cт3
    """
    message = mess.text
    message = message.split(' ')
    
    number = []
    name = []
    height = []
    quantity = []
    steel = []

    if len(message) > 2:
        number.append(message[0])
        name.append(message[1])
        height.append(message[2].split('мм')[0])
        steel.append(message[2].split('мм')[1])
        try:   
            quantity.append(message[3].split('шт')[0])
        except:
            quantity.append(message[4].split('шт')[0])
        
        
        return number, name, height, quantity, steel
        
    else: 
        number.append(message[0])
        quantity.append(message[1])   


        return number, quantity
    

print(colored('[OK]', 'green'))
bot.polling()