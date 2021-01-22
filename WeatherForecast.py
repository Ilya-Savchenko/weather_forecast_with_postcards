from datetime import datetime, timedelta

import WeatherMaker as wm


def get_forecast():
	print('За какой диапазон дат вы хотите получить данные?\n'
	      'Вводите их в формате ГГГГ.ММ.ДД')
	first_day = input('Первый день диапазона\n>>>').split('.')
	last_day = input('Последний день диапазона\n>>>').split('.')
	forecast = db.get_data_in_db(first_day, last_day)
	if forecast:
		for elem in forecast:
			print(f'{str(elem[0])} температура "{elem[1]}", погода: {elem[2]}')


def create_postcard():
	print('За какой диапазон дат вы хотите создать открытки?\n'
	      'Вводите их в формате ГГГГ.ММ.ДД')
	first_day = input('Первый день диапазона\n>>>').split('.')
	last_day = input('Последний день диапазона\n>>>').split('.')
	forecast = db.get_data_in_db(first_day, last_day)
	if forecast:
		for elem in forecast:
			draftsman = wm.ImageMaker()
			draftsman.create_postcard(elem)


def action():
	act = input('\nВыберите какое действие вы хотите сделать?\n'
	            '1 - Показать прогнозы за диапазон дат\n'
	            '2 - Создать открытки с прогнозами\n'
	            '>>>')
	if 0 < int(act) <= len(actions):
		actions[int(act) - 1]()
	else:
		raise ValueError('Введен неверный номер')


def start_application():
	global db
	today = datetime.now().date()
	five_days_back = str(today - timedelta(days=4)).split('-')
	forecast = wm.WeatherMaker()
	forecast_data = forecast.get_forecast()
	db = wm.DatabaseUpdater()
	db.save_data_in_db(forecast_data)
	forecast_for_last_five_days = db.get_data_in_db(first_day=five_days_back, last_day=str(today).split('-'))
	print('Прогноз погоды за последние пять дней:')
	for elem in forecast_for_last_five_days:
		print(f'{str(elem[0])} была температура "{elem[1]}" - {elem[2]}')


actions = [get_forecast, create_postcard]

if __name__ == '__main__':
	try:
		start_application()
		action()
	except ValueError as ve:
		print(ve)
		print('Перезапустите')
