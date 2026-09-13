from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.exceptions import ValidationError

from airport.models import (
    Ticket,
    Flight,
    AirplaneType,
    Airplane,
    Country,
    City,
    Airport,
    Route,
    Order,
)


class TestRouteModel(TestCase):
    def setUp(self):
        self.country = Country.objects.create(name="Ukraine", code="+380")

        self.city_lviv = City.objects.create(name="Lviv", country=self.country)
        self.city_kyiv = City.objects.create(name="Kyiv", country=self.country)
        self.airport_source = Airport.objects.create(
            name="Danylo Halytskyi International Airport",
            closest_big_city=self.city_lviv,
        )
        self.airport_destination = Airport.objects.create(
            name="Boryspil International Airport",
            closest_big_city=self.city_kyiv,
        )

        self.route = Route.objects.create(
            source=self.airport_source,
            destination=self.airport_destination,
            distance=1000,
        )

    def test_unique_route(self):

        with self.assertRaises(ValidationError):
            Route.objects.create(
                source=self.airport_source,
                destination=self.airport_destination,
                distance=1000,
            )


class TicketModelTest(TestCase):
    def setUp(self):
        self.country = Country.objects.create(name="Ukraine", code="+380")

        self.city_lviv = City.objects.create(name="Lviv", country=self.country)
        self.city_kyiv = City.objects.create(name="Kyiv", country=self.country)

        self.airport_source = Airport.objects.create(
            name="Danylo Halytskyi International Airport",
            closest_big_city=self.city_lviv,
        )
        self.airport_destination = Airport.objects.create(
            name="Boryspil International Airport",
            closest_big_city=self.city_kyiv,
        )

        self.route = Route.objects.create(
            source=self.airport_source,
            destination=self.airport_destination,
            distance=1000,
        )

        self.airplane_type = AirplaneType.objects.create(name="Airbus")
        self.airplane = Airplane.objects.create(
            name="Airbus A320",
            rows=20,
            seats_in_row=30,
            airplane_type=self.airplane_type,
        )

        self.flight = Flight.objects.create(
            route=self.route,
            airplane=self.airplane,
            departure_time="2026-09-17T11:00:00Z",
            arrival_time="2026-09-17T14:00:00Z",
        )

        self.user = get_user_model().objects.create_user(
            email="test@test.com",
            password="1qazcde3",
        )
        self.order = Order.objects.create(user=self.user)

        self.ticket = Ticket.objects.create(
            row=1,
            seat=13,
            flight=self.flight,
            order=self.order,
        )

    def test_ticket_created_with_correct_fields(self):
        self.assertEqual(self.ticket.row, 1)
        self.assertEqual(self.ticket.seat, 13)
        self.assertEqual(self.ticket.flight, self.flight)
        self.assertEqual(self.ticket.order, self.order)

    def test_ticket_created_with_not_correct_row(self):
        with self.assertRaises(ValidationError):
            Ticket.objects.create(
                row=21,
                seat=29,
                flight=self.flight,
                order=self.order,
            )

    def test_ticket_created_with_not_correct_seat(self):
        with self.assertRaises(ValidationError):
            Ticket.objects.create(
                row=19,
                seat=31,
                flight=self.flight,
                order=self.order,
            )

    def test_duplicate_ticket(self):
        with self.assertRaises(ValidationError):
            Ticket.objects.create(
                row=1,
                seat=13,
                flight=self.flight,
                order=self.order,
            )

    def test_duplicate_ticket_in_other_flight(self):
        flight = Flight.objects.create(
            route=self.route,
            airplane=self.airplane,
            departure_time="2026-09-17T17:00:00Z",
            arrival_time="2026-09-17T20:00:00Z",
        )
        ticket = Ticket.objects.create(
            row=1,
            seat=13,
            flight=flight,
            order=self.order,
        )
        self.assertIsNotNone(ticket.pk)
