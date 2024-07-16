from django.contrib import admin

from pets.models import Pet,Product,Cart

# Register your models here.class product_admin(admin.ModelAdmin):
class Pet_admin(admin.ModelAdmin):
    list_display=['id','name','age','breed','description','image','price','quantity']
    list_filter=['price','breed']

class Product_admin(admin.ModelAdmin):
    list_display=['id','name','description','image','price','quantity']
    list_filter=['price']

admin.site.register(Pet,Pet_admin)
admin.site.register(Product,Product_admin)
admin.site.register(Cart)
