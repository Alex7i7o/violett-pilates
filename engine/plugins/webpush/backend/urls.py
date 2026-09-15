from django.urls import path
from .views import SubscribeView

urlpatterns = [
    path('webpush/subscribe/', SubscribeView.as_view(), name='webpush_subscribe'),
]