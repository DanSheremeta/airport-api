import tempfile
import os

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from airport.models import Flight, Route, Airport, Airplane, AirplaneType
from airport.serializers import AirplaneSerializer, AirplaneListSerializer

AIRPLANE_URL = reverse("airport:airplane-list")
FLIGHT_URL = reverse("airport:flight-list")


def sample_airplane_type(**params):
    defaults = {
        "name": "Airplane Type",
    }
    defaults.update(params)

    return AirplaneType.objects.create(**defaults)

def sample_airplane(**params):
    airplane_type = sample_airplane_type()

    defaults = {
        "name": "Airplane",
        "rows": 10,
        "seats_in_row": "4",
        "airplane_type": airplane_type,
    }
    defaults.update(params)

    return Airplane.objects.create(**defaults)


def image_upload_url(airplane_id):
    """Return URL for airplane image upload"""
    return reverse("airport:airplane-upload-image", args=[airplane_id])


def detail_url(flight_id):
    return reverse("airport:airplane-detail", args=[flight_id])


class UnauthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(AIRPLANE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedMovieApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_airplanes(self):
        sample_airplane()
        sample_airplane()

        res = self.client.get(AIRPLANE_URL)

        airplanes = Airplane.objects.order_by("id")
        serializer = AirplaneListSerializer(airplanes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_airplanes_by_type_ids(self):
        type1 = sample_airplane_type(name="Type 1")
        type2 = sample_airplane_type(name="Type 2")

        airplane1 = sample_airplane(
            name="Airplane 1",
            rows=10,
            seats_in_row=4,
            airplane_type=type1,
        )
        airplane2 = sample_airplane(
            name="Airplane 2",
            rows=10,
            seats_in_row=4,
            airplane_type=type2,
        )
        airplane3 = sample_airplane(name="Airplane 3")

        res = self.client.get(
            AIRPLANE_URL, {"airplane_types": f"{type1.id},{type2.id}"}
        )

        serializer1 = AirplaneListSerializer(airplane1)
        serializer2 = AirplaneListSerializer(airplane2)
        serializer3 = AirplaneListSerializer(airplane3)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_filter_airplanes_by_name(self):
        airplane1 = sample_airplane(
            name="Airplane Test 1",
            rows=10,
            seats_in_row=4,
        )
        airplane2 = sample_airplane(
            name="Airplane Test 2",
            rows=10,
            seats_in_row=4,
        )
        airplane3 = sample_airplane(name="Airplane 3")

        res = self.client.get(AIRPLANE_URL, {"name": "Test"})

        serializer1 = AirplaneListSerializer(airplane1)
        serializer2 = AirplaneListSerializer(airplane2)
        serializer3 = AirplaneListSerializer(airplane3)

        self.assertIn(serializer1.data, res.data["results"])
        self.assertIn(serializer2.data, res.data["results"])
        self.assertNotIn(serializer3.data, res.data["results"])

    def test_retrieve_airplane_detail(self):
        airplane = sample_airplane(
            rows=10,
            seats_in_row=4,
        )

        url = detail_url(airplane.id)
        res = self.client.get(url)

        serializer = AirplaneListSerializer(airplane)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_airplane_forbidden(self):
        payload = {
            "name": "Test Airplane",
            "rows": 10,
            "seats_in_row": 10,
            "airplane_type": sample_airplane_type(),
        }
        res = self.client.post(AIRPLANE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirplaneApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "password", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_airplane(self):
        _type = sample_airplane_type()
        payload = {
            "name": "Airplane 1",
            "rows": 10,
            "seats_in_row": 4,
            "airplane_type": _type.id,
        }
        res = self.client.post(AIRPLANE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        payload["airplane_type"] = _type
        airplane = Airplane.objects.get(id=res.data["id"])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(airplane, key))


class AirplaneImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin@myproject.com", "password"
        )
        self.client.force_authenticate(self.user)
        self.airplane_type = sample_airplane_type(name="Type 1")
        self.airplane = sample_airplane(
            airplane_type=self.airplane_type
        )

    def tearDown(self):
        self.airplane.airplane_image.delete()

    def test_upload_image_to_airplane(self):
        url = image_upload_url(self.airplane.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"airplane_image": ntf}, format="multipart")
        self.airplane.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("airplane_image", res.data)
        self.assertTrue(os.path.exists(self.airplane.airplane_image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.airplane.id)
        res = self.client.post(url, {"airplane_image": "not image"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_image_to_airplane_list_should_not_work(self):
        url = AIRPLANE_URL
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                url,
                {
                    "name": "Airplane",
                    "row": 10,
                    "seats_in_row": 5,
                    "airplane_type": sample_airplane_type().id,
                    "airplane_image": ntf,
                },
                format="multipart",
            )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        airplane = Airplane.objects.get(name="Airplane")
        self.assertFalse(airplane.airplane_image)

    def test_image_url_is_shown_on_airplane_detail(self):
        url = image_upload_url(self.airplane.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"airplane_image": ntf}, format="multipart")
        res = self.client.get(detail_url(self.airplane.id))

        self.assertIn("airplane_image", res.data)

    def test_image_url_is_shown_on_airplane_list(self):
        url = image_upload_url(self.airplane.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"airplane_image": ntf}, format="multipart")
        res = self.client.get(AIRPLANE_URL)

        self.assertIn("airplane_image", res.data["results"][0].keys())

    def test_image_url_is_shown_on_flight_list(self):
        url = image_upload_url(self.airplane.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"airplane_image": ntf}, format="multipart")

        flight = Flight.objects.create(
            route=Route.objects.create(
                source=Airport.objects.create(
                    name="Test 1",
                    city="city",
                    country="country",
                    icao_code="CODE",
                    iata_code="COD",
                ),
                destination=Airport.objects.create(
                    name="Test 2",
                    city="city",
                    country="country",
                    icao_code="CODE",
                    iata_code="COD",
                ),
                distance=1000,
            ),
            airplane=self.airplane,
            departure_time="2024-04-01T11:00:00",
            arrival_time="2024-04-01T14:10:00",
        )
        res = self.client.get(FLIGHT_URL)

        self.assertIn("airplane_image", res.data["results"][0]["airplane"].keys())

    def test_put_airplane_not_allowed(self):
        payload = {
            "name": "Airplane",
            "rows": 10,
            "seats_in_row": 4,
            "airplane_type": sample_airplane(),
        }

        airplane = sample_airplane()
        url = detail_url(airplane.id)

        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_airplane_not_allowed(self):
        airplane = sample_airplane()
        url = detail_url(airplane.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
