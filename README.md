# Телеграм бот "Авидей"
## Предназначение
Бот сравнивает цены двух метапоисковиков авиабилетов — Авиасейлс и Авиабилет.
## Устройство
Файл [IATA_town_cod.py](https://github.com/zakhar-petukhov/telegram_avia_bot/blob/master/IATA_town_cod.py) содержит в себе коды аэропортов IATA.

Пользователь вводит город вылета, город прилета и дату в формате - Москва Пенза 23.05.2018

Класс ```Checking_cities_and_dates``` проверяет на валидность вводимые данные и после отправляет в классы:```Search_tickets_in_the_company_skyscanner``` и ```Search_tickets_in_the_company_aviabilet```, где при помощи парсера Beautiful Soup выявляются цены с сайтов.

Основным является класс ```Combined_search```, в нем осуществляется сравнение цен и отправка сообщений пользователям.

![Пример работы](https://i.ibb.co/6BcGfKD/photo-2018-12-14-18-27-27.jpg)
