from datetime import datetime
from django.urls import include, path, register_converter
from rest_framework import routers
from web.api.views import (
    CityCouncilAgendaView,
    CityCouncilAttendanceListView,
    GazetteView,
    GazetteEventsView,
    HealthCheckView,
)


class DateConverter:
    regex = '\d{4}-\d{2}-\d{2}'

    def to_python(self, value):
        return datetime.strptime(value, '%Y-%m-%d')

    def to_url(self, value):
        return value


register_converter(DateConverter, 'yyyy')

router = routers.DefaultRouter()
router.register("", HealthCheckView, basename="root")
router.register("gazettes", GazetteView, basename="gazettes")


urlpatterns = [
    path("", include(router.urls)),
    path(
        "city-council/agenda/",
        CityCouncilAgendaView.as_view(),
        name="city-council-agenda",
    ),
    path(
        "city-council/attendance-list/",
        CityCouncilAttendanceListView.as_view(),
        name="city-council-attendance-list",
    ),
    path(
        "gazette_events/<yyyy:date>",
        GazetteEventsView.as_view(),
        name="gazette-events"
    ),
]
