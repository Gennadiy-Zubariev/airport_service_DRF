from django.contrib import admin

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


class TicketInLine(admin.TabularInline):
    model = Ticket
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = (TicketInLine,)


admin.register(Country)
admin.register(City)
admin.register(Airport)
admin.register(Airplane)
admin.register(AirplaneType)
admin.register(Crew)
admin.register(Route)
admin.register(Flight)
