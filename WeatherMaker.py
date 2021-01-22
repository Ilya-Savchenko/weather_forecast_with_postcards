import os
from datetime import date, datetime, timedelta

import cv2
import lxml.html as lh
import requests
from playhouse.db_url import connect

import DBInitialization


class WeatherMaker:
	MONTHS = {
		'янв': 1,
		'февр': 2,
		'мар': 3,
		'апр': 4,
		'май': 5,
		'июнь': 6,
		'июль': 7,
		'авг': 8,
		'сент': 9,
		'окт': 10,
		'нояб': 11,
		'дек': 12,
	}

	def __init__(self):
		self.weather_url = 'https://yandex.ru/pogoda/213?via=srp'
		self.data_of_weather = {}

	def get_forecast(self):
		weather_response = requests.get(self.weather_url).text
		html_three = lh.document_fromstring(weather_response)
		forecast_dates = html_three.xpath('//*[@class="time forecast-briefly__date"]/text()')
		weather = html_three.xpath('//*[@class="forecast-briefly__condition"]/text()')
		temp_value = html_three.xpath('//*[@class="temp__value"]/text()')[3::2]
		for i in range(len(forecast_dates)):
			day, month = int(forecast_dates[i].split(' ')[0]), forecast_dates[i].split(' ')[1]
			month = self.MONTHS[month]
			year = self._determine_year(month)
			forecast_date = date(day=day, month=month, year=year)
			self.data_of_weather[forecast_dates[i]] = {
				'Погода': weather[i],
				'Температура': temp_value[i],
				'Дата': forecast_date
			}
		return self.data_of_weather

	@staticmethod
	def _determine_year(month: int):
		if datetime.now().month == 12 and month == 1:
			return datetime.now().year + 1
		elif datetime.now().month == 1 and month == 12:
			return datetime.now().year - 1
		else:
			return datetime.now().year


class ImageMaker:

	def __init__(self):
		self.weather = {
			'снег': 'weather_img/snow.jpg',
			'облачн': 'weather_img/cloud.jpg',
			'пасмурн': 'weather_img/cloud.jpg',
			'ясно': 'weather_img/sun.jpg',
			'дождь': 'weather_img/rain.jpg'
		}

	def create_postcard(self, forecast_for_date: ()):
		f_date = forecast_for_date[0]
		f_temp = forecast_for_date[1]
		f_weather = forecast_for_date[2]
		self.get_gradient_background(f_weather)
		img = self._insert_forecast_image_on_postcard(f_weather)
		img = self._add_text_in_postcard(img, f_date, f_temp, f_weather)
		self._save_postcard_with_forecast(img, f_date)

	def get_gradient_background(self, weather):
		weather = weather.lower()
		img = cv2.imread('forecast_base.jpg')
		height, width, _ = img.shape
		cv2.line(img, (1000, 100), (1000, 2000), (0, 255, 0), 10)
		r = 255
		g = 255
		b = 255
		for i in range(width + height, 0, -1):
			cv2.line(img, (i, 0), (0, i), (b, g, r), 2)
			if i % 3 == 0:
				if 'ясно' in weather:
					b -= 1
				elif 'облачн' in weather or 'пасмурн' in weather:
					if i < 690:
						g -= 1
						b -= 1
						r -= 1
				elif 'снег' in weather:
					r -= 1
				elif 'дождь' in weather:
					r -= 2
					g -= 1
				else:
					print('Невозможно создать фон')
					break
			cv2.imwrite('forecast_background.jpg', img)

	def _insert_forecast_image_on_postcard(self, weather):
		img1 = cv2.imread('forecast_background.jpg')
		for key in self.weather.keys():
			if key in weather.lower():
				img2 = cv2.imread(self.weather[key])
				rows, cols, channels = img2.shape
				roi = img1[0:rows, 0:cols]
				img2gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
				ret, mask = cv2.threshold(img2gray, 10, 255, cv2.THRESH_BINARY)
				mask_inv = cv2.bitwise_not(mask)
				img1_bg = cv2.bitwise_and(roi, roi, mask=mask_inv)
				img2_fg = cv2.bitwise_and(img2, img2, mask=mask)
				dst = cv2.add(img1_bg, img2_fg)
				img1[0:rows, 0:cols] = dst
				return img1
		else:
			print('Неправильный ввод')

	def _save_postcard_with_forecast(self, img, f_date):
		if not os.path.exists('forecasts'):
			os.makedirs('forecasts')
		filename = f'forecasts/forecast_for_{f_date}.jpg'
		cv2.imshow('res', img)
		cv2.waitKey(0)
		cv2.destroyAllWindows()
		cv2.imwrite(filename, img)

	def _add_text_in_postcard(self, img, f_date, f_temp, f_weather):
		date_text = str(f_date)
		temp_text = str(f_temp)
		if temp_text[0].isdigit():
			temp_text = f'{f_temp}C'
		else:
			temp_text = f'-{temp_text[1:]}C'
		weather_text = str(f_weather)
		font = cv2.FONT_HERSHEY_COMPLEX
		color = (0, 34, 200)
		cv2.putText(img, temp_text, (120, 85), fontFace=font, fontScale=3, color=color, thickness=2)
		cv2.putText(img, weather_text, (20, 140), fontFace=font, fontScale=1, color=color, thickness=2)
		cv2.putText(img, date_text, (20, 200), fontFace=font, fontScale=2, color=color, thickness=2)
		return img


class DatabaseUpdater:

	def __init__(self, db_url='sqlite:///WeatherForecast.db'):

		self.database = connect(db_url)
		DBInitialization.db.initialize(self.database)
		self.weather = DBInitialization.Forecast
		self.weather.create_table()

	def get_data_in_db(self, first_day: [], last_day: []):
		forecast_for_dates = []
		try:
			first_day = date(year=int(first_day[0]), month=int(first_day[1]), day=int(first_day[2]))
			last_day = date(year=int(last_day[0]), month=int(last_day[1]), day=int(last_day[2]))
			if first_day > last_day:
				raise ValueError
		except ValueError:
			print('Введена несуществующая дата или неправильный диапазон! Повторите ввод')
		else:
			for forecast_for_day in self.weather.select().where(self.weather.f_date >= first_day):
				if forecast_for_day.f_date <= last_day:
					forecast_for_dates.append(
						(forecast_for_day.f_date,
						 forecast_for_day.f_temp,
						 forecast_for_day.f_weather))
			return self._check_info_in_db(forecast_for_dates, first_day, last_day)

	def _check_info_in_db(self, forecast_for_dates, first_day, last_day):
		if len(forecast_for_dates) == 0:
			print('Информация по выбранным датам отсутствует в базе')
			return
		elif forecast_for_dates[0][0] > first_day:
			print(f'По одной или нескольким дат в указанном диапазоне отсутствует информация в базе. '
			      f'Присутствуют данные с {forecast_for_dates[0][0]}, а вы ввели {first_day}')
			return
		elif forecast_for_dates[-1][0] < last_day:
			print(f'По одной или нескольким дат в указанном диапазоне отсутствует информация в базе. '
			      f'Присутствуют данные до {forecast_for_dates[-1][0]}, а вы ввели {first_day}')
			return
		return forecast_for_dates

	def save_data_in_db(self, data: {}):
		predicted_days = []
		four_days_back = datetime.today() - timedelta(days=5)
		for forecast_for_day in self.weather.select().where(self.weather.f_date > four_days_back.date()):
			predicted_days.append(forecast_for_day.f_date)

		for value in data.values():
			if value['Дата'] in predicted_days:
				continue
			self.weather.create(
				f_date=value['Дата'],
				f_temp=value['Температура'],
				f_weather=value['Погода']
			)
