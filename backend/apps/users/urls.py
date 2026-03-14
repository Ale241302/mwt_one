from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.UserListCreateView.as_view(), name='user-list-create'),
    path('<int:user_id>/', views.UserDetailView.as_view(), name='user-detail'),
    path('<int:user_id>/permissions/', views.UserPermissionsView.as_view(), name='user-permissions'),
]
