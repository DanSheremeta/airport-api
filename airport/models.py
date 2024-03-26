import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext as _


class Crew(models.Model):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name}"

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


def airplane_image_file_path(instance, filename):
    _, extension = os.path.splitext(filename)
    filename = f"{slugify(instance.name)}-{uuid.uuid4()}{extension}"

    return os.path.join("uploads/airplanes/", filename)


class Airplane(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey(
        AirplaneType,
        on_delete=models.CASCADE,
        related_name="airplanes",
    )
    airplane_image = models.ImageField(
        null=True,
        upload_to=airplane_image_file_path,
    )

    class Meta:
        ordering = ("name",)

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

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

    @staticmethod
    def validate_ticket(row, seat, airplane, error_to_raise):
        for ticket_attr_value, ticket_attr_name, airplane_attr_name in [
            (row, "row", "rows"),
            (seat, "seat", "seats_in_row"),
        ]:
            count_attrs = getattr(airplane, airplane_attr_name)
            if not (1 <= ticket_attr_value <= count_attrs):
                raise error_to_raise(
                    {
                        ticket_attr_name: f"{ticket_attr_name} "
                                          f"number must be in available range: "
                                          f"(1, {airplane_attr_name}): "
                                          f"(1, {count_attrs})"
                    }
                )

    def clean(self):
        Ticket.validate_ticket(
            self.row,
            self.seat,
            self.flight.airplane,
            ValidationError,
        )

    def save(
            self,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None,
    ):
        self.full_clean()
        return super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )

    def __str__(self):
        return (
            f"{str(self.flight)} (row: {self.row}, seat: {self.seat})"
        )

    class Meta:
        unique_together = ("flight", "row", "seat")
        ordering = ["flight", "row", "seat"]
