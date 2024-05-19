import logging
import re
import paramiko
import os
from dotenv import load_dotenv
from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, CallbackQueryHandler
import psycopg2
from psycopg2 import Error
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, \
    CallbackQueryHandler
from telegram.ext import CommandHandler, MessageHandler, Filters, ConversationHandler

load_dotenv()
TOKEN = os.getenv('TOKEN')
GET_ALL_PACKAGES, GET_PACKAGE_INFO = range(2)
GET_PHONE_NUMBERS, CONFIRM_PHONE_NUMBERS = range(2)
CONFIRM_EMAIL  = range(2)


# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')


def helpCommand(update: Update, context):
    update.message.reply_text('Help!')


def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'findPhoneNumbers'

def findemailCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска email: ')

    return 'findemail'

def verify_passwordCommand(update: Update, context):
    update.message.reply_text('Введите пароль для проверки: ')

    return 'verify_password'

def findPhoneNumbers (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий(или нет) номера телефонов

    phoneNumRegex = re.compile(r"\+?7[ -]?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{2}[ -]?\d{2}|\+?7[ -]?\d{10}|\+?7[ -]?\d{3}[ -]?\d{3}[ -]?\d{4}|8[ -]?\(?\d{3}\)?[ -]?\d{3}[ -]?\d{2}[ -]?\d{2}|8[ -]?\d{10}|8[ -]?\d{3}[ -]?\d{3}[ -]?\d{4}") 

    phoneNumberList = phoneNumRegex.findall(user_input) # Ищем номера телефонов

    context.user_data['phone_numbers'] = phoneNumberList
    if not phoneNumberList: # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return # Завершаем выполнение функции
    phoneNumbers = ''
    for i, phone_number in enumerate(phoneNumberList, start=1):
        phoneNumbers += f'{i}. {phone_number}\n'

    update.message.reply_text(phoneNumbers)

    # Создаем кнопки для пользовательского ввода
    keyboard = [[KeyboardButton("Записать в базу данных"), KeyboardButton("Отказаться")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

    return CONFIRM_PHONE_NUMBERS
        
def confirmPhoneNumbers(update: Update, context):
    
    user_input = update.message.text
    load_dotenv()
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    database = os.getenv('DB_DATABASE')
    if user_input == 'Записать в базу данных':
        try:
            connection = psycopg2.connect(user=username,
                                        password=password,
                                        host=host,
                                        port=port, 
                                        database=database)
            cursor = connection.cursor()
            phoneNumbers = context.user_data.get('phone_numbers', [])
            print(phoneNumbers)
            for phone_number in phoneNumbers:
                cursor.execute(f"INSERT INTO phone (phone) VALUES ('{phone_number}');")
            connection.commit()
            update.message.reply_text('Номера успешно записаны в базу данных!')
            logging.info("Команда успешно выполнена")
        except (Exception, Error) as error:
            logging.error("Ошибка при работе с PostgreSQL: %s", error)
            update.message.reply_text('Ошибка при добавлении номеров в базу данных')
        finally:
            if connection is not None:
                cursor.close()
                connection.close()
                logging.info("Соединение с PostgreSQL закрыто")
        return ConversationHandler.END

    elif user_input == 'Отказаться':
        update.message.reply_text("Вы отказались от записи номеров в базу данных.")
        return ConversationHandler.END

    else:
        update.message.reply_text("Пожалуйста, используйте кнопки для выбора действия.")
        return CONFIRM_PHONE_NUMBERS   
    
       
# зарегаем новое состояние и функцию обработки состояния в ConversationHandler
conv_handler_confirm_phone_numbers = ConversationHandler(
    entry_points=[CommandHandler('find_phone_number', findPhoneNumbers)],
    states={
        'confirm_phone_numbers': [MessageHandler(Filters.text & ~Filters.command, confirmPhoneNumbers)],
    },
    fallbacks=[]
)

def findemail (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий(или нет) email

    emailList = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', user_input) # Ищем email
    context.user_data['EMAILS'] = emailList
    if not emailList: # Обрабатываем случай, когда  email net
        update.message.reply_text('email не найдены')
        return # Завершаем выполнение функции
    
    emails = '' # Создаем строку, в которую будем записывать email
    for i in range(len(emailList)):
        emails += f'{i+1}. {emailList[i]}\n' # Записываем email
    update.message.reply_text(emails) # Отправляем сообщение пользователю
    # Создаем кнопки для пользовательского ввода
    keyboard = [[KeyboardButton("Записать в базу данных"), KeyboardButton("Отказаться")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

    return CONFIRM_EMAIL

def confiremail(update: Update, context):
    user_input = update.message.text
    load_dotenv()
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    database = os.getenv('DB_DATABASE')
    if user_input == 'Записать в базу данных':
        try:
            connection = psycopg2.connect(user=username,
                                    password=password,
                                    host=host,
                                    port=port, 
                                    database=database)
            cursor = connection.cursor()

            emails = context.user_data.get('EMAILS', [])
            print(emails)
            for email in emails:
                cursor.execute(f"INSERT INTO mail (mail) VALUES ('{email}');")
            connection.commit()
            update.message.reply_text('Email успешно добавлен!')
            logging.info("Команда успешно выполнена")
        except (Exception, Error) as error:
            logging.error("Ошибка при работе с PostgreSQL: %s", error)
            update.message.reply_text('Ошибка при добавлении Email в базу данных')
        finally:
            if connection is not None:
                cursor.close()
                connection.close()
                logging.info("Соединение с PostgreSQL закрыто")
        return ConversationHandler.END

    elif user_input == 'Отказаться':
        update.message.reply_text("Вы отказались от записи Email в базу данных.")
        return ConversationHandler.END

    else:
        update.message.reply_text("Пожалуйста, используйте кнопки для выбора действия.")
        return CONFIRM_EMAIL  
    
       
# зарегаем новое состояние и функцию обработки состояния в ConversationHandler
conv_handler_confirm_email = ConversationHandler(
    entry_points=[CommandHandler('find_email', findemail)],
    states={
        'confirm_email': [MessageHandler(Filters.text & ~Filters.command, confiremail)],
    },
    fallbacks=[]
)

def verify_password (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий(или нет) password
    if re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()])[A-Za-z\d!@#$%^&*()]{8,}$', user_input):
        update.message.reply_text('Пароль сложный')
    else:
        update.message.reply_text('Пароль простой')
    return ConversationHandler.END

def echo(update: Update, context):
    update.message.reply_text(update.message.text)

def ssh_command(hostname, port, username, password, command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port, username, password)
    stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode()
    client.close()
    return output



def get_release(update: Update, context):
    
    load_dotenv()
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('cat /etc/*release')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    print(data)
    update.message.reply_text(data)
    return ConversationHandler.END

def get_uname(update: Update, context):
    
    load_dotenv()
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')


    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('uname -a')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    print(data)
    update.message.reply_text(data)
    return ConversationHandler.END

def get_uptime(update: Update, context):
    
    load_dotenv()
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('uptime')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    print(data)
    update.message.reply_text(data)
    return ConversationHandler.END

def get_df(update: Update, context):
    
    load_dotenv()
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('df')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    print(data)
    update.message.reply_text(data)
    return ConversationHandler.END

def get_free(update: Update, context):
    
    load_dotenv()
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('free -h')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    print(data)
    update.message.reply_text(data)
    return ConversationHandler.END

def get_mpstat(update: Update, context):
    
    load_dotenv()
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('mpstat')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    print(data)
    update.message.reply_text(data)
    return ConversationHandler.END

def get_w(update: Update, context):
    
    load_dotenv()
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('w')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    print(data)
    update.message.reply_text(data)
    return ConversationHandler.END

def get_auths(update: Update, context):
    
    load_dotenv()
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('last -10')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    print(data)
    update.message.reply_text(data)
    return ConversationHandler.END

def get_critical(update: Update, context):
    
    load_dotenv()
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('journalctl -p crit -n 5')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    print(data)
    update.message.reply_text(data)
    return ConversationHandler.END

def get_ps(update: Update, context):
    
    load_dotenv()
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('ps aux | tail -n 20')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    print(data)
    update.message.reply_text(data)
    return ConversationHandler.END

def get_ss(update: Update, context):
    
    load_dotenv()
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('ss -tuln')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    print(data)
    update.message.reply_text(data)
    return ConversationHandler.END

def get_apt_list(update: Update, context):
    
    keyboard = [[InlineKeyboardButton('1. Вывести все пакеты', callback_data='get_all_packages'), InlineKeyboardButton('2. Поиск по названию', callback_data='get_package_info')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Выберите вариант:', reply_markup=reply_markup)
    return GET_ALL_PACKAGES

def get_all_packages(update: Update, context):
    
    load_dotenv()
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('dpkg -l | tail -n 20')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    print(data)
    update.callback_query.edit_message_text(text=data)
    return ConversationHandler.END

def get_package_info(update: Update, context: CallbackContext):
    update.callback_query.message.reply_text('Введите название пакета:')
    return GET_PACKAGE_INFO

def search_package_info(update: Update, context):
    
    load_dotenv()
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    package_name = update.message.text
    stdin, stdout, stderr = client.exec_command(f'dpkg -l | grep {package_name}')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    print(data)
    update.message.reply_text(data)
    return ConversationHandler.END

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    choice = query.data
    if choice == 'get_all_packages':
        get_all_packages(update, context)
    elif choice == 'get_package_info':
        get_package_info(update, context)

def get_services(update: Update, context):
    
    load_dotenv()
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('systemctl list-units --type=service | tail -n 20')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    print(data)
    update.message.reply_text(data)
    return ConversationHandler.END


def get_emails(update: Update, context):
    load_dotenv()
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    database = os.getenv('DB_DATABASE')
    connection = None
    try:
        connection = psycopg2.connect(user=username,
                                    password=password,
                                    host=host,
                                    port=port, 
                                    database=database)

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM mail;")
        data = cursor.fetchall()
        for row in data:
            print(row)
        update.message.reply_text(data)      
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
        return ConversationHandler.END    

def get_phone_numbers(update: Update, context):
    load_dotenv()
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    database = os.getenv('DB_DATABASE')
    connection = None
    try:
        connection = psycopg2.connect(user=username,
                                    password=password,
                                    host=host,
                                    port=port, 
                                    database=database)

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM phone;")
        data = cursor.fetchall()
        for row in data:
            print(row)
        update.message.reply_text(data)         
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
        return ConversationHandler.END
    

def get_repl_logs(update: Update, context):
    try:
        log_lines = get_log_lines(20)
        update.message.reply_text(log_lines)
        return ConversationHandler.END
    except Exception as e:
        update.message.reply_text(f"Error: {e}")
        return ConversationHandler.END

def get_log_lines(limit):
    load_dotenv()
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    database = os.getenv('DB_DATABASE')
    connection = None
    try:
        connection = psycopg2.connect(user=username,
                                    password=password,
                                    host=host,
                                    port=port, 
                                    database=database)

        cursor = connection.cursor()
        cursor.execute("SELECT pg_read_file('/var/log/postgresql/postgresql.log') AS log_content;")
        result = cursor.fetchone()
        if result:
            log_content = result[0]
            # Split log content into lines
            lines = log_content.split('\n')
            # Filter lines containing "replication" (case insensitive)
            replication_lines = [line for line in lines if 'replication' in line.lower()]
            # Return only the first 'limit' lines
            return '\n'.join(replication_lines[:limit])
        else:
            return "File content not found"
    except (Exception, Error) as error:
        return f"Error retrieving file content: {error}"
    finally:
        if connection is not None:
            cursor.close()
            connection.close()

def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога телефон
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'findPhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            CONFIRM_PHONE_NUMBERS: [MessageHandler(Filters.text & ~Filters.command, confirmPhoneNumbers)],
        },
        fallbacks=[]
    )
    # Обработчик диалога email

    convHandleremail = ConversationHandler(
        entry_points=[CommandHandler('find_email', findemailCommand)],
        states={
            'findemail': [MessageHandler(Filters.text & ~Filters.command, findemail)],
            CONFIRM_EMAIL: [MessageHandler(Filters.text & ~Filters.command, confiremail)],
        },
        fallbacks=[]
    )
	# Обработчик диалога password
    convHandlerpassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verify_passwordCommand)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verify_password)],
        },
        fallbacks=[]
    )	
    
	# Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandleremail)
    dp.add_handler(convHandlerpassword)
    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_services", get_services))
    dp.add_handler(CommandHandler('get_apt_list', get_apt_list))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, search_package_info))
    dp.add_handler(CommandHandler('get_repl_logs', get_repl_logs))
    dp.add_handler(CommandHandler('get_emails', get_emails))
    dp.add_handler(CommandHandler('get_phone_numbers', get_phone_numbers))
    
    
		
	# Регистрируем обработчик текстовых сообщений
    #dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
		
	# Запускаем бота
    updater.start_polling()

	# Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()