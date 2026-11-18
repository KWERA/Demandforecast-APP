from django.conf import settings
from django.db import models


class Dataset(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='datasets')
    name = models.CharField(max_length=100)
    file = models.FileField(upload_to='datasets/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class ForecastRun(models.Model):
    """One model's result for one dataset (e.g. Prophet on 'Bottled Water')."""
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='runs')
    model_name = models.CharField(max_length=50)
    mae = models.FloatField(null=True, blank=True)
    rmse = models.FloatField(null=True, blank=True)
    mape = models.FloatField(null=True, blank=True)
    is_best = models.BooleanField(default=False)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def accuracy(self):
        if self.mape is None:
            return None
        return round(max(0, 100 - self.mape), 1)

    def __str__(self):
        return f"{self.model_name} on {self.dataset.name}"


class ForecastPoint(models.Model):
    """One predicted month. kind is 'test' (last 6 known months) or 'future'."""
    run = models.ForeignKey(ForecastRun, on_delete=models.CASCADE, related_name='points')
    kind = models.CharField(max_length=10)
    date = models.DateField()
    predicted = models.FloatField()
    lower = models.FloatField(null=True, blank=True)
    upper = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['date']
