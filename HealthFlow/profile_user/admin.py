from django.contrib import admin
from .models import Specialist, SpecialistApplication, Note, Blood, Pressure, BMI

admin.site.register(Specialist)
admin.site.register(SpecialistApplication)
admin.site.register(Note)
admin.site.register(Blood)
admin.site.register(Pressure)
admin.site.register(BMI)