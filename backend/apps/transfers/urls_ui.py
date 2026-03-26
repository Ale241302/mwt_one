from django.urls import path
from .views_ui import TransfersUIView

app_name = 'transfers-ui'

urlpatterns = [
    path('', TransfersUIView.as_view(), name='list'),
]
