from django.db import models
from django.db.models.constraints import UniqueConstraint

from airport_service import settings

from airport.utils.helpers import airplane_image_path


class Country(models.Model):
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=10, unique=True)

    class Meta:
        verbose_name_plural = "countries"
        ordering = ("name",)

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=255)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="cities")

    class Meta:
        verbose_name_plural = "cities"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Airport(models.Model):
    name = models.CharField(max_length=255)
    closest_big_city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="airports")

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} ({self.closest_big_city})"


class AirplaneType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Airplane(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey(AirplaneType, on_delete=models.CASCADE, related_name="airplanes")
    image = models.ImageField(null=True, upload_to=airplane_image_path)

    class Meta:
        ordering = ("name",)

    @property
    def capacity(self):
        return self.seats_in_row * self.rows

    def __str__(self):
        return f"{self.name} (capacity: {self.capacity})"


class Crew(models.Model):
    first_name = models.CharField(max_length=63)
    last_name = models.CharField(max_length=63)

    class Meta:
        verbose_name_plural = "crew"
        ordering = ("last_name", "first_name")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Route(models.Model):
    source = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="routes_from")
    destination = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="routes_to")
    distance = models.IntegerField(db_index=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["source", "destination"], name="unique_sourse_destination_route")
        ]
        ordering = ("source",)

    def __str__(self):
        return f"FROM {self.source} - TO {self.destination} ({self.distance} km.)"


class Flight(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="flights")
    airplane = models.ForeignKey(Airplane, on_delete=models.CASCADE, related_name="airplanes")
    crew = models.ManyToManyField(Crew, related_name="crew", blank=True)
    departure_time = models.DateTimeField(db_index=True)
    arrival_time = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ("-departure_time")

    def __str__(self):
        return (
            f"{self.route} ({self.airplane}, "
            f"{self.departure_time.strftime('%Y-%m-%d %H:%M')})"
        )

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ("user",)

    def __str__(self):
        return f"Order №{self.id} - by {self.user}(created at {self.created_at})"


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    flight = models.ForeignKey(
        Flight, on_delete=models.CASCADE, related_name="tickets"
    )
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="tickets"
    )

    class Meta:
        constraints = [
            UniqueConstraint(fields=["flight", "row", "seat"], name="unique_ticket_flight_row_seat")
        ]
        ordering = ["row", "seat"]

    def __str__(self):
        return (
            f"Ticket {self.flight.route} "
            f"(row: {self.row}, seat: {self.seat})"
        )

    def clean(self):
        from django.core.exceptions import ValidationError

        airplane = self.flight.airplane
        if not (1 <= self.row <= airplane.rows):
            raise ValidationError(
                {"row": f"Row must be between 1 and {airplane.rows}."}
            )
        if not (1 <= self.seat <= airplane.seats_in_row):
            raise ValidationError(
                {"seat": f"Seat must be between 1 and {airplane.seats_in_row}."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


