from django.urls import path
from . import views

urlpatterns = [
    path('ask/', views.AskView.as_view(), name='knowledge-ask'),
    path('index/', views.IndexKBView.as_view(), name='knowledge-index'),
    path('search/', views.SearchView.as_view(), name='knowledge-search'),
    path('sessions/', views.SessionListView.as_view(), name='knowledge-sessions'),
    path('sessions/<str:session_id>/', views.SessionDetailView.as_view(), name='knowledge-session-detail'),
]
