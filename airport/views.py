from django.db.models import F, Count
from rest_framework import mixins
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from airport.permissions import IsAdminOrIfAuthenticatedReadOnly
from airport.models import (
    Crew,
    Airport,
    Airplane,
    Route,
    Flight, Order,
)
from airport.serializers import (
    CrewSerializer,
    AirportSerializer,
    AirplaneSerializer,
    AirplaneListSerializer,
    RouteSerializer,
    RouteDetailSerializer,
    FlightSerializer,
    FlightListSerializer,
    FlightDetailSerializer,
    OrderSerializer,
    OrderListSerializer,
)


class DefaultPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class CrewViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class AirportViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer
    pagination_class = DefaultPagination
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class AirplaneViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = Airplane.objects.all()
    pagination_class = DefaultPagination
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer
        return AirplaneSerializer


class RouteViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    queryset = Route.objects.all()
    pagination_class = DefaultPagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return RouteDetailSerializer

        return RouteSerializer


class FlightViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet
):
    queryset = (
        Flight.objects.all()
        .select_related("route", "airplane")
        .prefetch_related("crew")
        .annotate(
            tickets_available=(
                F("airplane__rows") * F("airplane__seats_in_row")
                - Count("tickets")
            )
        )
    )
    pagination_class = DefaultPagination
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    @staticmethod
    def _params_to_ints(qs):
        """Converts a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        """Retrieve the flights with filters"""
        airplanes = self.request.query_params.get("airplains")
        routes = self.request.query_params.get("routes")
        date = self.request.query_params.get("date")

        queryset = self.queryset

        if airplanes:
            airplanes_ids = self._params_to_ints(airplanes)
            queryset = queryset.filter(airplane__id_in=airplanes_ids)

        if routes:
            routes_ids = self._params_to_ints(routes)
            queryset = queryset.filter(route__id__in=routes_ids)

        if date:
            queryset = queryset.filter(departure_time__date=date)

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer

        if self.action == "retrieve":
            return FlightDetailSerializer

        return FlightSerializer


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = (
        Order.objects
        .select_related("tickets__flight__airplane", "tickets__flight__route")
        .prefetch_related("tickets__flight__crew")
    )
    serializer_class = OrderSerializer
    pagination_class = DefaultPagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
