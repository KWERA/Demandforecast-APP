from django.contrib import admin
from .models import Dataset, ForecastRun, ForecastPoint

admin.site.register(Dataset)
admin.site.register(ForecastRun)
admin.site.register(ForecastPoint)
