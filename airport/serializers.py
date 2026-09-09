from django.db import transaction
from rest_framework import serializers
from airport.models import (
    Country,
    City,
    Airport,
    Airplane,
    AirplaneType,
    Crew,
    Route,
    Flight,
    Order,
    Ticket
)


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ("id", "name", "code")


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("id", "name", "country")


class CityListSerializer(CitySerializer):
    country = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name"
    )


class CityRetrieveSerializer(CitySerializer):
    country = CountrySerializer(read_only=True)


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("id", "name", "closest_big_city")

class AirportListSerializer(AirportSerializer):
    closest_big_city = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name"
    )

class AirportRetrieveSerializer(AirportSerializer):
    closest_big_city = CityRetrieveSerializer(read_only=True)



class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ("id", "name")


class AirplaneSerializer(serializers.ModelSerializer):
    capacity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Airplane
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "airplane_type",
            "capacity",
            "image"
        )

class AirplaneListSerializer(AirplaneSerializer):
    airplane_type = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name"
    )


class AirplaneRetrieveSerializer(AirplaneSerializer):
    airplane_type = AirplaneSerializer(read_only=True)


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "role")

class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")

class RouteListSerializer(RouteSerializer):
    source = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name"
    )
    destination = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name"
    )

class RouteRetrieveSerializer(RouteSerializer):
    source = AirportRetrieveSerializer(read_only=True)
    destination = AirportRetrieveSerializer(read_only=True)


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "crew",
            "departure_time",
            "arrival_time"
        )


class FlightListSerializer(FlightSerializer):
    route = serializers.StringRelatedField()
    airplane = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name"
    )
    tickets_available = serializers.SerializerMethodField(
        method_name="tickets_available"
    )

    class Meta(FlightSerializer.Meta):
        fields = FlightSerializer.Meta.fields + ("tickets_available",)


    def tickets_available(self, obj):
        return obj.airplane.capacity - obj.tickets.count()

class FlightRetrieveSerializer(FlightSerializer):
    route = RouteRetrieveSerializer(read_only=True)
    airplane = AirplaneRetrieveSerializer(read_only=True)
    crew = CrewSerializer(many=True, read_only=True)
    taken_seats = serializers.SerializerMethodField(
        method_name="get_taken_seats"
    )

    class Meta(FlightSerializer.Meta):
        fields = FlightSerializer.Meta.fields + ("taken_seats",)

    def get_taken_seats(self, obj):
        return list(obj.tickets.values_list("row", "seat"))


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight", "order")

    def validate(self, attrs):
        Ticket.validate_seat(
            attrs["seat"],
            attrs["flight"].airplane.seats_in_row,
            serializers.ValidationError
        )
        Ticket.validate_row(
            attrs["row"],
            attrs["flight"].airplane.rows,
            serializers.ValidationError
        )
        return attrs


class TicketDetailSerializer(TicketSerializer):
    flight = FlightListSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("id", "created_at")

class OrderListSerializer(OrderSerializer):
    tickets = serializers.SerializerMethodField(
        method_name="get_tickets_count"
    )
    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + ("tickets",)

    def get_tickets_count(self, obj):
        return obj.tickets.count()

class OrderRetrieveSerializer(OrderSerializer):
    tickets = TicketDetailSerializer(read_only=True, many=True)

class OrderCreateSerializer(OrderSerializer):
    tickets = TicketSerializer(many=True)

    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + ("tickets",)

    def create(self, validation_data):
        tickets_data = validation_data.pop("tickets")
        with transaction.atomic():
            order = Order.objects.create(**validation_data)
            for ticket in tickets_data:
                Ticket.objects.create(order=order, **ticket)
        return order





