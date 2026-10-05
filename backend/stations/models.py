from django.db import models


class Station(models.Model):
    opis_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=2)
    price = models.DecimalField(max_digits=6, decimal_places=3)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return f"{self.name}, {self.city}, {self.state}"
