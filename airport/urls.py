from django.urls import path, include
from rest_framework import routers

from airport.views import (
    AirportViewSet,
    CountryViewSet,
    CityViewSet,
    AirplaneTypeViewSet,
    AirplaneViewSet,
    RouteViewSet,
    FlightViewSet,
    OrderViewSet, CrewViewSet
)


app_name = "airport"

router = routers.DefaultRouter()

router.register("countries", CountryViewSet)
router.register("cities", CityViewSet)
router.register("airports", AirportViewSet)
router.register("airplane-types", AirplaneTypeViewSet)
router.register("airplanes", AirplaneViewSet)
router.register("routes", RouteViewSet)
router.register("flights", FlightViewSet)
router.register("orders", OrderViewSet, basename="order")
router.register("crew", CrewViewSet)

urlpatterns = [
    path("",include(router.urls))
]