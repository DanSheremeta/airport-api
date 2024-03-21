from django.conf import settings
from django.db import models
from django.utils.translation import gettext as _

class Crew(models.Model):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class Airport(models.Model):
    AIRPORT_TYPES_CHOICES = (
        ("civilian", "Civilian"),
        ("military", "Military"),
        ("cargo", "Cargo"),
    )

    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    airport_type = models.CharField(
        max_length=50,
        default="civilian",
        choices=AIRPORT_TYPES_CHOICES
    )
    icao_code = models.CharField(max_length=4)
    iata_code = models.CharField(max_length=3)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Route(models.Model):
    source = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="routes_from",
    )
    destination = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="routes_to",
    )
    distance = models.IntegerField()

    class Meta:
        ordering = ("source", "destination")

    def __str__(self):
        return f"Route {self.source}-{self.destination}"


class AirplaneType(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Airplane(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey(
        AirplaneType,
        on_delete=models.CASCADE,
        related_name="airplanes",
    )

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} ({self.airplane_type})"

class Flight(models.Model):
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="flights",
    )
    airplane = models.ForeignKey(
        Airplane,
        on_delete=models.CASCADE,
        related_name="flights",
    )
    crew = models.ManyToManyField(
        Crew,
        related_name="flights",
        blank=True,
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    class Meta:
        verbose_name = _("flight")
        verbose_name_plural = _("flights")
        ordering = ("departure_time",)

    def __str__(self):
        return f"Flight: {str(self.route)}"


class Order(models.Model):
    created_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"Order of {self.user.email}, time: {self.created_at}"


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="tickets",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets",
    )

    def __str__(self):
        return (
            f"{str(self.flight)} (row: {self.row}, seat: {self.seat})"
        )

    class Meta:
        unique_together = ("flight", "row", "seat")
        ordering = ["flight", "row", "seat"]
