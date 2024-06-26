from django.contrib.auth import get_user_model
from rest_framework import serializers

from airport.serializers import OrderListSerializer


class UserSerializer(serializers.ModelSerializer):
    orders = OrderListSerializer(many=True, read_only=True)

    class Meta:
        model = get_user_model()
        fields = ("id", "email", "first_name", "last_name", "avatar", "orders", "password", "is_staff")
        read_only_fields = ("is_staff", "avatar")
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data):
        """Create a new user with encrypted password and return it"""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update a user, set the password correctly and return it"""
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()

        return user


class UserImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "avatar")
