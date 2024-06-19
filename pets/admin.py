from django.contrib import admin

from pets.models import Pet,Product,Cart

# Register your models here.
admin.site.register(Pet)
admin.site.register(Product)
admin.site.register(Cart)