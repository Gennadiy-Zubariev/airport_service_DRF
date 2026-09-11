from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from rest_framework.test import APIClient

from airport.models import (
    Ticket,
    Flight,
    AirplaneType,
    Airplane,
    Country,
    City,
    Airport,
    Route,
    Order
)

from airport.serializers import (
    CountrySerializer,
    CitySerializer,
    CityListSerializer,
    CityRetrieveSerializer,
    AirportSerializer,
    AirportListSerializer,
    AirportRetrieveSerializer,
    AirplaneTypeSerializer,
    AirplaneSerializer, AirplaneListSerializer, AirplaneRetrieveSerializer, CrewSerializer, RouteSerializer,
    RouteListSerializer, RouteRetrieveSerializer, FlightSerializer, FlightListSerializer, FlightRetrieveSerializer,
    OrderSerializer, OrderListSerializer, OrderRetrieveSerializer, OrderCreateSerializer, AirplaneImageSerializer
)


TICKET_URL = reverse("airport:order-list")
FLIGHT_URL = reverse("airport:flight-list")
AIRPLANE_URL = reverse("airport:airplane-list")
ROUTE_URL = reverse("airport:route-list")

def flight_detail_url(flight_id):
    return reverse("airport:flight-detail", args=[flight_id])

def order_detail_url(order_id):
    return reverse("airport:order-detail", args=[order_id])


class UnauthenticatedAirportAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TICKET_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirportAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.test",
            password="testpassword"
        )
        self.client.force_authenticate(self.user)

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

    def test_flight_list(self):
        Flight.objects.create(
            route=self.route,
            airplane=self.airplane,
            departure_time="2026-09-20T11:00:00Z",
            arrival_time="2026-09-20T14:00:00Z",
        )
        result = self.client.get(FLIGHT_URL)
        flights = Flight.objects.all()
        serializer = FlightListSerializer(flights, many=True)

        self.assertEqual(result.data["results"], serializer.data)
        self.assertEqual(result.status_code, status.HTTP_200_OK)

    def test_create_order(self):
        payload = {
            "tickets": [
                {"row": 1, "seat": 9, "flight": self.flight.id}
            ]
        }
        result = self.client.post(TICKET_URL, payload, format="json")
        self.assertEqual(result.status_code, status.HTTP_201_CREATED)

    def test_order_isolation_between_users(self):
        other_user = get_user_model().objects.create_user(
            email="other@test.test",
            password="testpassword",
        )
        other_order = Order.objects.create(user=other_user)
        Ticket.objects.create(
            flight=self.flight,
            row=1,
            seat=5,
            order=other_order,
        )

        list_result = self.client.get(TICKET_URL)
        order_ids = [order["id"] for order in list_result.data["results"]]
        self.assertNotIn(other_order.id, order_ids)

        detail_result = self.client.get(order_detail_url(other_order.id))
        self.assertEqual(detail_result.status_code, status.HTTP_404_NOT_FOUND)

    def test_tickets_available(self):
        order = Order.objects.create(user=self.user)
        num_tickets = 3
        for  i in range(num_tickets):
            Ticket.objects.create(
                flight=self.flight,
                row=1,
                seat=i + 1,
                order=order
            )
        result = self.client.get(FLIGHT_URL)
        self.assertEqual(
            result.data["results"][0]["tickets_available"],
            self.flight.airplane.capacity - num_tickets,
        )

    def test_tickets_taken_seats(self):
        order = Order.objects.create(user=self.user)
        num_tickets = 3
        for i in range(num_tickets):
            Ticket.objects.create(
                flight=self.flight,
                row=1,
                seat=i + 1,
                order=order
            )
        result = self.client.get(flight_detail_url(self.flight.id))
        self.assertEqual(
            result.data["taken_seats"],
            list(self.flight.f_tickets.values_list("row", "seat"))
        )

    def test_validation_seat_in_ticket_serializer(self):
        payload = {
            "tickets": [
                {"row": 1, "seat": 99, "flight": self.flight.id}
            ]
        }
        result = self.client.post(TICKET_URL, payload, format="json")
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_validation_row_in_ticket_serializer(self):
        payload = {
            "tickets": [
                {"row": 99, "seat": 1, "flight": self.flight.id}
            ]
        }
        result = self.client.post(TICKET_URL, payload, format="json")
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_airplane_filter_by_airplane_type(self):
        airplane_type_1 = AirplaneType.objects.create(name="Embraer")
        airplane_type_2 = AirplaneType.objects.create(name="Boeing")
        airplane_1 = Airplane.objects.create(
            name="A34",
            rows=10,
            seats_in_row=5,
            airplane_type=airplane_type_1
        )
        airplane_2 = Airplane.objects.create(
            name="A34",
            rows=10,
            seats_in_row=5,
            airplane_type=airplane_type_2
        )

        result = self.client.get(AIRPLANE_URL, {"airplane_type": airplane_type_1.id})

        serializer_1 = AirplaneListSerializer(airplane_1)
        serializer_2 = AirplaneListSerializer(airplane_2)

        self.assertIn(serializer_1.data, result.data["results"])
        self.assertNotIn(serializer_2.data, result.data["results"])


    def test_flight_filter_by_source_destination_departure_date(self):
        source_airport_1 = Airport.objects.create(
            name="Boryspil",
            closest_big_city=self.city_kyiv)
        sourse_airport_2 = Airport.objects.create(
            name="Danylo Halytskyi",
            closest_big_city=self.city_lviv)
        destination_airport_1 = Airport.objects.create(
            name="Danylo Halytskyi",
            closest_big_city=self.city_lviv)
        destination_airport_2 = Airport.objects.create(
            name="Boryspil",
            closest_big_city=self.city_kyiv)

        route_1 = Route.objects.create(
            source=source_airport_1,
            destination=destination_airport_1,
            distance=1000
        )
        route_2 = Route.objects.create(
            source=sourse_airport_2,
            destination=destination_airport_2,
            distance=1000
        )

        flight_1 = Flight.objects.create(
            route=route_1,
            airplane=self.airplane,
            departure_time="2026-09-17T11:00:00Z",
            arrival_time="2026-09-17T14:00:00Z"
        )
        flight_2 = Flight.objects.create(
            route=route_2,
            airplane=self.airplane,
            departure_time="2026-09-16T08:00:00Z",
            arrival_time="2026-09-16T10:30:00Z"
        )

        serializer_1 = FlightListSerializer(flight_1)
        serializer_2 = FlightListSerializer(flight_2)

        with self.subTest("filter by source"):
            result = self.client.get(FLIGHT_URL, {"source": "Kyiv"})
            self.assertIn(serializer_1.data, result.data["results"])
            self.assertNotIn(serializer_2.data, result.data["results"])

        with self.subTest("filter by destination"):
            result = self.client.get(FLIGHT_URL, {"destination": "Lviv"})
            self.assertIn(serializer_1.data, result.data["results"])
            self.assertNotIn(serializer_2.data, result.data["results"])

        with self.subTest("filter by departure_date"):
            result = self.client.get(FLIGHT_URL, {"departure_date": "2026-09-17"})
            self.assertIn(serializer_1.data, result.data["results"])
            self.assertNotIn(serializer_2.data, result.data["results"])


    def test_route_filter_by_city(self):
        city_odesa = City.objects.create(name="Odesa", country=self.country)
        airport_odesa = Airport.objects.create(
            name="Odesa International Airport",
            closest_big_city=city_odesa,
        )
        other_route = Route.objects.create(
            source=airport_odesa,
            destination=self.airport_destination,
            distance=500,
        )

        result = self.client.get(ROUTE_URL, {"city": self.city_lviv.id})

        serializer_1 = RouteListSerializer(self.route)
        serializer_2 = RouteListSerializer(other_route)

        self.assertIn(serializer_1.data, result.data["results"])
        self.assertNotIn(serializer_2.data, result.data["results"])


class AdminAirportAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

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

        self.payload = {
            "route": self.route.id,
            "airplane": self.airplane.id,
            "crew": [],
            "departure_time": "2026-09-17T11:00:00Z",
            "arrival_time": "2026-09-17T14:00:00Z",
        }

    def test_authenticated_user_cannot_create_flight(self):
        user = get_user_model().objects.create_user(
            email="regular@test.com",
            password="testpassword",
        )
        self.client.force_authenticate(user)

        result = self.client.post(FLIGHT_URL, self.payload, format="json")

        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Flight.objects.count(), 0)

    def test_admin_can_create_and_update_flight(self):
        admin = get_user_model().objects.create_user(
            email="admin@test.com",
            password="testpassword",
            is_staff=True,
        )
        self.client.force_authenticate(admin)

        create_result = self.client.post(FLIGHT_URL, self.payload, format="json")
        self.assertEqual(create_result.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Flight.objects.count(), 1)

        flight = Flight.objects.get(id=create_result.data["id"])

        update_result = self.client.patch(
            flight_detail_url(flight.id),
            {"departure_time": "2026-09-18T09:00:00Z"},
            format="json",
        )
        self.assertEqual(update_result.status_code, status.HTTP_200_OK)

        flight.refresh_from_db()
        self.assertEqual(
            flight.departure_time.isoformat(),
            "2026-09-18T09:00:00+00:00",
        )

