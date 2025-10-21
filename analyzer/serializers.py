from rest_framework import serializers
from .models import StringEntry

class StringEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = StringEntry
        fields = ["id", "value", "properties", "created_at"]
        read_only_fields = ["id", "properties", "created_at"]

class CreateStringSerializer(serializers.Serializer):
    value = serializers.CharField()
