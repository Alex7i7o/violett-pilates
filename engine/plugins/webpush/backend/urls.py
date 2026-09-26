from django.urls import path
from .views import SubscribeView, TestWebPushView

urlpatterns = [
    path('subscribe/', SubscribeView.as_view(), name='webpush-subscribe'),
    path('test/', TestWebPushView.as_view(), name='webpush-test'),
]
