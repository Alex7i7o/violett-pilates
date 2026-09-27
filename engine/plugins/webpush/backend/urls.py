from django.urls import path
from .views import SubscribeView, TestWebPushView

urlpatterns = [
    path('webpush/subscribe/', SubscribeView.as_view(), name='webpush-subscribe'),
    path('webpush/test/', TestWebPushView.as_view(), name='webpush-test'),
]
