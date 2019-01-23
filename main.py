import datetime
import cherrypy

import telebot
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

import config
import IATA_town_cod

WEBHOOK_HOST = '178.128.179.123'
WEBHOOK_PORT = 443  # 443, 80, 88 или 8443 (порт должен быть открыт!)
WEBHOOK_LISTEN = '0.0.0.0'  # На некоторых серверах придется указывать такой же IP, что и выше

WEBHOOK_SSL_CERT = './webhook_cert.pem'
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % config.token

token = config.token
bot = telebot.TeleBot(token)


class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                'content-type' in cherrypy.request.headers and \
                cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)


class Checking_cities_and_dates:
    def __init__(self, message):
        self.text = message.text
        self.chat_id = message.chat.id
        self.dict_town = IATA_town_cod.town
        self.division_text = message.text.split(' ')  # ['Москва', 'Архангельск', '8.07.2018']

    def departure(self):
        if self.division_text[0] in self.dict_town:
            departure_cod_town = self.dict_town.get(self.division_text[0])
            print(departure_cod_town)
            return departure_cod_town
        else:
            bot.send_message(self.chat_id, '''
Ты неправильно написал название города или его еще нет в моей базе!''')
            return None

    def landing(self):
        if self.division_text[1] in self.dict_town:
            lending_cod_town = self.dict_town.get(self.division_text[1])
            print(lending_cod_town)
            return lending_cod_town
        else:
            bot.send_message(self.chat_id, '''
Ты неправильно написал название города или его еще нет в моей базе!''')
            return None

    def data(self):
        try:
            data_sorting = self.division_text[2]
            data_check = datetime.datetime.strptime(data_sorting, '%d.%m.%Y').strftime('%d.%m.%Y')
            print(data_check)
            return data_check
        except Exception:
            bot.send_message(self.chat_id, '''
Упс, что-то пошло не так!
Кажется, ты ошибся с датой.
Пример: 15.10.2018''')
            return None


class Search_tickets_in_the_company_aviabilet:
    def __init__(self, message):
        self.room_for_sum = []
        self.text = message.text
        self.chat_id = message.chat.id
        self.url_for_parser_aviabilet = 'https://search.aviabilet7.ru/flights/'
        self.url_for_user_aviabilet = []
        self.answer = Checking_cities_and_dates(message)

    def data_for_aviabilet(self):
        data_sorting = self.answer.data()
        if '.' in data_sorting:
            data_sorting = data_sorting.replace('.', '')
        data_sorting = data_sorting[:4]
        print(data_sorting)
        return data_sorting

    def link_for_parser(self):
        give_parse_url_for_parser = self.url_for_parser_aviabilet + self.answer.departure() + \
                                    self.data_for_aviabilet() + self.answer.landing() + '1'
        self.url_for_user_aviabilet.append(give_parse_url_for_parser)
        return give_parse_url_for_parser

    def ticket_price(self):
        try:
            opts = Options()
            opts.set_headless()
            assert opts.headless
            driver = webdriver.Firefox(options=opts)
            driver.get(self.link_for_parser())
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            heading = soup.find('span', {'class': 'currency_font currency_font--rub'})
            word_processing = ''.join(heading.text.split())
            self.room_for_sum.append(word_processing)
            print(word_processing)
            driver.close()
            return word_processing
        except Exception:
            return Exception


class Search_tickets_in_the_company_skyscanner:
    def __init__(self, message):
        self.text = message.text
        self.chat_id = message.chat.id
        self.url_for_parser = 'https://www.skyscanner.ru/transport/flights/{}/{}/{}#results'
        self.url_for_user = []
        self.room_for_sum = []
        self.answer = Checking_cities_and_dates(message)

    def data_for_skyscanner(self):
        data_sorting = self.answer.data()
        if '.' in data_sorting:
            data_sorting = data_sorting.replace('.', '-')
        text_processing_in_the_list = data_sorting.split('-')
        text_wrapping_processing = text_processing_in_the_list[::-1]
        processed_text = '-'.join(text_wrapping_processing)
        return processed_text

    def link_for_parser(self):
        give_parse_url_for_parser = self.url_for_parser.format(self.answer.departure(),
                                                               self.answer.landing(),
                                                               self.data_for_skyscanner())
        self.url_for_user.append(give_parse_url_for_parser)
        return give_parse_url_for_parser

    def ticket_price(self):
        try:
            opts = Options()
            opts.set_headless()
            assert opts.headless
            driver = webdriver.Firefox(options=opts)
            driver.get(self.link_for_parser())
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            heading = soup.find('span', {'class': 'fqs-price'})
            word_processing = ''.join(heading.text.split())
            letters_processing = word_processing[:-2]
            print(letters_processing)
            self.room_for_sum.append(letters_processing)
            driver.close()
            return letters_processing
        except Exception:
            return Exception


class Combined_search:
    def __init__(self, message):
        self.text = message.text
        self.chat_id = message.chat.id
        self.answer_aviabilet = Search_tickets_in_the_company_aviabilet(message)
        self.answer_skyscanner = Search_tickets_in_the_company_skyscanner(message)
        self.a = Checking_cities_and_dates(message)

    def answer(self):
        bot.send_message(self.chat_id, '''
Смотри, что получилось: 
1). Отправляемся из: {} 
2). Прилетаем в: {}
3). Дата: {}'''.format(self.a.division_text[0], self.a.division_text[1],
                       self.a.division_text[2]))
        bot.send_message(self.chat_id, 'Я уже ищу! Это займет 20-30 секунд!')
        price_list_aviabilet = self.answer_aviabilet.ticket_price()
        price_list_skyscanner = self.answer_skyscanner.ticket_price()
        if (price_list_aviabilet and price_list_skyscanner) != Exception:
            if self.answer_aviabilet.room_for_sum[0] < self.answer_skyscanner.room_for_sum[0]:
                bot.send_message(self.chat_id, '''
Выгодная цена: {} рублей. 
Кликните по ссылке: {}, чтобы купить билет'''.format(self.answer_aviabilet.room_for_sum[0],
                                                     self.answer_aviabilet.url_for_user_aviabilet[0]))
            else:
                bot.send_message(self.chat_id, '''
Выгодная цена: {} рублей. 
Кликните по ссылке: {}, чтобы купить билет'''.format(self.answer_skyscanner.room_for_sum[0],
                                                     self.answer_skyscanner.url_for_user[0]))
        else:
            bot.send_message(self.chat_id, '''
Ошибка!
Возможно самолет не летает по таким городам.''')


@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, """Привет! Меня зовут Авидей. 

Я умею искать и сравнивать цены ведущих поисковиков (Aviasales, Skyscanner, Yandex и другие).

Тебе больше не нужно открывать десятки вкладок в браузере. Просто сообщи мне, куда и\
когда полетишь — а я предложу самый дешевый авиабилет.
Напримеp: 'Москва Пенза 02.07.2018'
""")


@bot.message_handler(content_types=['text'])
def start_handler_parser(message):
    answer_not_start = Checking_cities_and_dates(message)
    combined_search = Combined_search(message)
    if (answer_not_start.departure() and answer_not_start.landing() and answer_not_start.data()) is None:
        pass
    else:
        combined_search.answer()


bot.remove_webhook()

bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV
})

cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
