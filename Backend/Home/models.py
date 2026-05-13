from django.db import models


class DemoRequest(models.Model):
    """Someone on the landing page asked for a demo."""
    name = models.CharField(max_length=120)
    email = models.EmailField()
    organization = models.CharField(max_length=120)
    phone = models.CharField(max_length=30, blank=True)
    message = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    contacted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} · {self.organization}"
