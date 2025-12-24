from django.urls import path
from . import views


urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payments/', views.payments, name='payments'),
    # Naya URL
    path('cash_on_delivery/<str:order_number>/', views.cash_on_delivery, name='cash_on_delivery'),
]
