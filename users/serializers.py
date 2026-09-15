from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "password", "is_staff")
        read_only_fields = ("id", "is_staff")

    def validate_email(self, value):
        value = value.strip().lower()
        matches = User.objects.filter(email__iexact=value)
        if self.instance:
            matches = matches.exclude(pk=self.instance.pk)
        if matches.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        if "password" in attrs:
            candidate = User(
                email=attrs.get("email", getattr(self.instance, "email", "")),
                first_name=attrs.get("first_name", getattr(self.instance, "first_name", "")),
                last_name=attrs.get("last_name", getattr(self.instance, "last_name", "")),
            )
            try:
                password_validation.validate_password(attrs["password"], candidate)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"password": exc.messages}) from exc
        return attrs

    def create(self, validated_data):
        try:
            with transaction.atomic():
                return User.objects.create_user(**validated_data)
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"email": "This email is already registered."}
            ) from exc

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if password is not None:
            instance.set_password(password)
        try:
            with transaction.atomic():
                instance.save()
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"email": "This email is already registered."}
            ) from exc
        return instance


class ProfileSerializer(UserSerializer):
    password = serializers.CharField(write_only=True, required=False, trim_whitespace=False)
