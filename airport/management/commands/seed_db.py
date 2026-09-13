import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from airport.models import (
    Airplane,
    AirplaneType,
    Airport,
    City,
    Country,
    Crew,
    Flight,
    Order,
    Route,
    Ticket,
)

COUNTRIES = [
    ("Ukraine", "UA"),
    ("Poland", "PL"),
    ("Germany", "DE"),
    ("France", "FR"),
    ("United States", "US"),
]

CITIES = [
    ("Kyiv", "Ukraine"),
    ("Lviv", "Ukraine"),
    ("Warsaw", "Poland"),
    ("Berlin", "Germany"),
    ("Paris", "France"),
    ("New York", "United States"),
]

AIRPORTS = [
    ("Boryspil International Airport", "Kyiv"),
    ("Lviv Danylo Halytskyi International Airport", "Lviv"),
    ("Warsaw Chopin Airport", "Warsaw"),
    ("Berlin Brandenburg Airport", "Berlin"),
    ("Charles de Gaulle Airport", "Paris"),
    ("John F. Kennedy International Airport", "New York"),
]

AIRPLANE_TYPES = ["Boeing 737", "Airbus A320", "Boeing 777", "Embraer E190"]

CREW = [
    ("Ivan", "Petrenko", Crew.Role.PILOT),
    ("Olena", "Kovalenko", Crew.Role.CO_PILOT),
    ("Maria", "Shevchenko", Crew.Role.FLIGHT_ATTENDANT),
    ("Andriy", "Bondarenko", Crew.Role.FLIGHT_ATTENDANT),
    ("Sergiy", "Tkachenko", Crew.Role.ENGINEER),
]

# (source airport, destination airport, distance km)
ROUTES = [
    ("Boryspil International Airport", "Warsaw Chopin Airport", 690),
    ("Warsaw Chopin Airport", "Boryspil International Airport", 690),
    ("Boryspil International Airport", "Berlin Brandenburg Airport", 1150),
    ("Berlin Brandenburg Airport", "Charles de Gaulle Airport", 880),
    (
        "Charles de Gaulle Airport",
        "John F. Kennedy International Airport",
        5850,
    ),
    (
        "Lviv Danylo Halytskyi International Airport",
        "Warsaw Chopin Airport",
        340,
    ),
]

DEMO_USER_EMAIL = "demo@example.com"
DEMO_USER_PASSWORD = "demo12345"


class Command(BaseCommand):
    help = ("Populate the database with "
            "demo data for the airport API (idempotent).")

    @transaction.atomic
    def handle(self, *args, **options):
        countries = self._seed_countries()
        cities = self._seed_cities(countries)
        airports = self._seed_airports(cities)
        airplane_types = self._seed_airplane_types()
        airplanes = self._seed_airplanes(airplane_types)
        crew = self._seed_crew()
        routes = self._seed_routes(airports)
        flights = self._seed_flights(routes, airplanes, crew)
        self._seed_demo_order(flights)

        self.stdout.write(self.style.SUCCESS("Database successfully seeded."))

    def _seed_countries(self):
        countries = {}
        for name, code in COUNTRIES:
            country, _ = Country.objects.get_or_create(
                name=name, defaults={"code": code}
            )
            countries[name] = country
        self.stdout.write(f"Countries: {len(countries)}")
        return countries

    def _seed_cities(self, countries):
        cities = {}
        for name, country_name in CITIES:
            city, _ = City.objects.get_or_create(
                name=name, country=countries[country_name]
            )
            cities[name] = city
        self.stdout.write(f"Cities: {len(cities)}")
        return cities

    def _seed_airports(self, cities):
        airports = {}
        for name, city_name in AIRPORTS:
            airport, _ = Airport.objects.get_or_create(
                name=name, defaults={"closest_big_city": cities[city_name]}
            )
            airports[name] = airport
        self.stdout.write(f"Airports: {len(airports)}")
        return airports

    def _seed_airplane_types(self):
        types = {}
        for name in AIRPLANE_TYPES:
            airplane_type, _ = AirplaneType.objects.get_or_create(name=name)
            types[name] = airplane_type
        self.stdout.write(f"Airplane types: {len(types)}")
        return types

    def _seed_airplanes(self, airplane_types):
        airplanes = []
        for i, (type_name, rows, seats_in_row) in enumerate(
            [
                ("Boeing 737", 30, 6),
                ("Airbus A320", 28, 6),
                ("Boeing 777", 45, 9),
                ("Embraer E190", 22, 4),
            ]
        ):
            airplane, _ = Airplane.objects.get_or_create(
                name=f"{type_name} #{i + 1}",
                defaults={
                    "rows": rows,
                    "seats_in_row": seats_in_row,
                    "airplane_type": airplane_types[type_name],
                },
            )
            airplanes.append(airplane)
        self.stdout.write(f"Airplanes: {len(airplanes)}")
        return airplanes

    def _seed_crew(self):
        crew = []
        for first_name, last_name, role in CREW:
            member, _ = Crew.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                defaults={"role": role},
            )
            crew.append(member)
        self.stdout.write(f"Crew members: {len(crew)}")
        return crew

    def _seed_routes(self, airports):
        routes = []
        for source_name, destination_name, distance in ROUTES:
            route, _ = Route.objects.get_or_create(
                source=airports[source_name],
                destination=airports[destination_name],
                defaults={"distance": distance},
            )
            routes.append(route)
        self.stdout.write(f"Routes: {len(routes)}")
        return routes

    def _seed_flights(self, routes, airplanes, crew):
        flights = []
        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        for i, route in enumerate(routes):
            departure_time = now + timedelta(days=i + 1, hours=i * 3)
            airplane = airplanes[i % len(airplanes)]
            flight, created = Flight.objects.get_or_create(
                route=route,
                airplane=airplane,
                departure_time=departure_time,
                defaults={
                    "arrival_time": departure_time
                    + timedelta(hours=2, minutes=30 * (i % 3)),
                },
            )
            if created:
                flight.crew.set(random.sample(crew, k=min(2, len(crew))))
            flights.append(flight)
        self.stdout.write(f"Flights: {len(flights)}")
        return flights

    def _seed_demo_order(self, flights):
        user_model = get_user_model()
        user, _ = user_model.objects.get_or_create(
            email=DEMO_USER_EMAIL,
        )
        if not user.has_usable_password():
            user.set_password(DEMO_USER_PASSWORD)
            user.save()

        if Order.objects.filter(user=user).exists():
            self.stdout.write("Demo order already exists, skipping.")
            return

        order = Order.objects.create(user=user)
        flight = flights[0]
        Ticket.objects.get_or_create(flight=flight, order=order, row=1, seat=1)
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo user: {DEMO_USER_EMAIL} / {DEMO_USER_PASSWORD} "
                f"with one order and one ticket."
            )
        )
