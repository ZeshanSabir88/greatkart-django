from django.contrib import admin
from .models import Payment, Order, OrderProduct

class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    fields = ('product', 'variations', 'user', 'payment', 'quantity', 'product_price', 'ordered')
    readonly_fields = ('payment', 'user', 'product', 'quantity', 'product_price', 'ordered')
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    # Jo fields aap ne maangi thi wo yahan list_display mein hain
    list_display = ['order_number', 'full_name', 'phone', 'email', 'city', 'order_total', 'status', 'is_ordered', 'created_at']
    list_filter = ['status', 'is_ordered']
    search_fields = ['order_number', 'first_name', 'last_name', 'phone', 'email']
    list_per_page = 20
    # Is se Order ke andar hi uske products nazar aayenge
    inlines = [OrderProductInline]

class OrderProductAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'user', 'quantity', 'product_price', 'ordered']
    list_filter = ['ordered']
    search_fields = ['order__order_number', 'product__product_name']

admin.site.register(Payment)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct, OrderProductAdmin)
