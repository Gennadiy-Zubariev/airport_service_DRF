from datetime import datetime

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from airport.utils.helpers import params_to_ints

from airport.models import (
    Country, City, Airport, AirplaneType, Airplane, Crew, Route, Flight, Order,

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


class CountryViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer


class CityViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = City.objects.all()

    serializer_class = CitySerializer

    def get_serializer_class(self):
        if self.action == "list":
            return CityListSerializer
        elif self.action == "retrieve":
            return CityRetrieveSerializer
        return CitySerializer

    def get_queryset(self):
        if self.action in ("list", "retrieve"):
            return self.queryset.select_related("country")
        return self.queryset


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return AirportListSerializer
        elif self.action == "retrieve":
            return AirportRetrieveSerializer
        return AirportSerializer

    def get_queryset(self):
        if self.action == "list":
            return self.queryset.select_related("closest_big_city")
        elif self.action == "retrieve":
            return self.queryset.select_related("closest_big_city__country")
        return self.queryset


class AirplaneTypeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer



class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer
        elif self.action == "retrieve":
            return AirplaneRetrieveSerializer
        elif self.action == "upload_image":
            return AirplaneImageSerializer
        return AirplaneSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related("airplane_type")
        airplane_type = self.request.query_params.get("airplane_type")
        if airplane_type:
            airplane_type = params_to_ints(airplane_type)
            queryset = queryset.filter(airplane_type__id__in=airplane_type)

        return queryset

    @action(
        methods=["POST",],
        detail=True,
        permission_classes=[IsAdminUser,],
        url_path="upload-image"
    )
    def upload_image(self, request, pk=None):
        airplane = self.get_object()
        serializer = self.get_serializer(airplane, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer

class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        if self.action == "retrieve":
            return RouteRetrieveSerializer
        return RouteSerializer

    def get_queryset(self):
        queryset = self.queryset

        if self.action == "list":
            queryset = queryset.select_related(
                "source__closest_big_city",
                "destination__closest_big_city",
            )

        elif self.action == "retrieve":
            queryset = queryset.select_related(
                "source__closest_big_city__country",
                "destination__closest_big_city__country",
            )

        return queryset



class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        elif self.action == "retrieve":
            return FlightRetrieveSerializer
        return FlightSerializer

    def get_queryset(self):
        queryset = self.queryset.prefetch_related("crew", "tickets")

        if self.action == "list":
            queryset = queryset.select_related(
                "route__source__closest_big_city",
                "route__destination__closest_big_city",
                "airplane",
            )
            source = self.request.query_params.get("source")
            destination = self.request.query_params.get("destination")
            departure_date = self.request.query_params.get("departure_date")
            if source:
                queryset = queryset.filter(
                    route__source__closest_big_city__name__icontains=source
                )
            if destination:
                queryset = queryset.filter(
                    route__destination__closest_big_city__name__icontains=destination
                )
            if departure_date:
                queryset = queryset.filter(
                    departure_time__date=datetime.strptime(
                        departure_date, "%Y-%m-%d"
                    ).date()
                )
        if self.action == "retrieve":
            queryset = queryset.select_related(
                "route__source__closest_big_city__country",
                "route__destination__closest_big_city__country",
                "airplane__airplane_type",
            )
        return queryset


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user)

        if self.action == "list":
            return queryset.prefetch_related("tickets")
        if self.action == "retrieve":
            return queryset.prefetch_related(
                "tickets__flight__airplane",
                "tickets__flight__route__source__closest_big_city",
                "tickets__flight__route__destination__closest_big_city",
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        if self.action == "retrieve":
            return OrderRetrieveSerializer
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)






