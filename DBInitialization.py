import peewee

db = peewee.DatabaseProxy()


class BaseModel(peewee.Model):
	class Meta:
		database = db


class Forecast(BaseModel):
	f_date = peewee.DateField(primary_key=True)
	f_temp = peewee.SmallIntegerField()
	f_weather = peewee.CharField()
