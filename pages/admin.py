from django.contrib import admin
from .models import Projects, Stocks, Events, Effects  # varsa diğer modeller


admin.site.register(Projects)
admin.site.register(Stocks)
admin.site.register(Events)
admin.site.register(Effects)
