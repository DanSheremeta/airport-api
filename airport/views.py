from django.db.models import F, Count, Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from airport.permissions import IsAdminOrIfAuthenticatedReadOnly
from airport.models import (
    Crew,
    Airport,
    Airplane,
    Route,
    Flight,
    Order, AirplaneType,
)
from airport.serializers import (
    CrewSerializer,
    AirportSerializer,
    AirplaneTypeSerializer,
    AirplaneSerializer,
    AirplaneListSerializer,
    AirplaneImageSerializer,
    RouteSerializer,
    RouteListSerializer,
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


class AirplaneTypeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class AirplaneViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = Airplane.objects.all().select_related("airplane_type")
    pagination_class = DefaultPagination
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return AirplaneListSerializer
        if self.action == "upload_image":
            return AirplaneImageSerializer
        return AirplaneSerializer

    @staticmethod
    def _params_to_ints(qs):
        """Converts a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_queryset(self):
        """Retrieve the airplanes with filters"""
        name = self.request.query_params.get("name")
        airplane_types = self.request.query_params.get("airplane_types")
        capacity_gte = self.request.query_params.get("capacity_gte")
        capacity_lte = self.request.query_params.get("capacity_lte")

        queryset = self.queryset.annotate(total_capacity=F("rows") * F("seats_in_row"))

        if name:
            queryset = queryset.filter(name__icontains=name)

        if airplane_types:
            airplane_type_ids = self._params_to_ints(airplane_types)
            queryset = queryset.filter(airplane_type__id__in=airplane_type_ids)

        if capacity_gte:
            queryset = queryset.filter(total_capacity__gte=capacity_gte)

        if capacity_lte:
            queryset = queryset.filter(total_capacity__lte=capacity_lte)

        return queryset.distinct()

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
        permission_classes=[IsAdminUser]
    )
    def upload_image(self, request, pk=None):
        item = self.get_object()
        serializer = self.get_serializer(item, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "airplane_types",
                type={"type": "list", "items": {"type": "number"}},
                description="Filter by airplane_type ids (ex. ?airplane_types=1,7)",
            ),
            OpenApiParameter(
                "name",
                type=OpenApiTypes.STR,
                description="Filter by airplane name (ex. ?name=boeing)",
            ),
            OpenApiParameter(
                "capacity_gte",
                type=OpenApiTypes.NUMBER,
                description="Filter by capacity greater than equals (ex. ?capacity_gte=100)",
            ),
            OpenApiParameter(
                "capacity_lte",
                type=OpenApiTypes.NUMBER,
                description="Filter by capacity less than equals (ex. ?capacity_lte=150)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class RouteViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    queryset = (
        Route.objects.all()
        .select_related("source", "destination")
    )
    pagination_class = DefaultPagination

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
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
        .select_related(
            "route__source",
            "route__destination",
            "airplane__airplane_type",
        )
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
        airplanes = self.request.query_params.get("airplanes")
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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "airplanes",
                type={"type": "list", "items": {"type": "number"}},
                description="Filter by airplane ids (ex. ?airplanes_ids=3,12)",
            ),
            OpenApiParameter(
                "routes",
                type={"type": "list", "items": {"type": "number"}},
                description="Filter by routes ids (ex. ?routes=4,7)",
            ),
            OpenApiParameter(
                "date",
                type=OpenApiTypes.DATE,
                description="Filter by flight date (ex. ?date=2024-05-01)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


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
