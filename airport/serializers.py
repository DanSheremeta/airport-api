from rest_framework import serializers

from airport.models import (
    Crew,
    Airport,
    Airplane,
    Route,
    Flight
)


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name")


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = (
            "id",
            "name",
            "city",
            "country",
            "airport_type",
            "icao_code",
            "iata_code",
        )


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "airplane_type",
        )


class AirplaneListSerializer(AirplaneSerializer):
    airplane_type = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )

    class Meta:
        model = Airplane
        fields = (
            "id",
            "name",
            "airplane_type",
            "capacity",
        )


class RouteSerializer(serializers.ModelSerializer):
    source = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )
    destination = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )

    class Meta:
        model = Route
        fields = (
            "id",
            "source",
            "destination",
            "distance",
        )


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "crew",
            "departure_time",
            "arrival_time",
        )


class FlightListSerializer(FlightSerializer):
    route_source = serializers.CharField(
        read_only=True, source="route.source.name"
    )
    route_destination = serializers.CharField(
        read_only=True, source="route.destination.name"
    )
    route_link = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name="airport:route-detail",
        source="route",
    )
    airplane = AirplaneListSerializer(many=False, read_only=True)
    crew = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Flight
        fields = (
            "id",
            "route_source",
            "route_destination",
            "route_link",
            "airplane",
            "crew",
            "departure_time",
            "arrival_time",
            "tickets_available",
        )


class FlightDetailSerializer(FlightSerializer):
    route = RouteSerializer(many=False, read_only=True)
    airplane = AirplaneSerializer(many=False, read_only=True)
    crew = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "crew",
            "departure_time",
            "arrival_time",
        )


class RouteDetailSerializer(RouteSerializer):
    flights = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name="airport:flight-detail",
    )

    class Meta:
        model = Route
        fields = (
            "id",
            "source",
            "destination",
            "distance",
            "flights",
        )
