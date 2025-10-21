from django.db import models
from django.utils import timezone

class StringEntry(models.Model):
    """
    Stores analyzed strings. Primary key is the SHA256 id for stable uniqueness.
    """
    id = models.CharField(max_length=64, primary_key=True)  # sha256 hex
    value = models.TextField()
    properties = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.id} - {self.value[:40]}"
