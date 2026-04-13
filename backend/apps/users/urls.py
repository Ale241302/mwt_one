from django.urls import path
from . import views
from .views_invitations import InviteClientView, AcceptInvitationView

urlpatterns = [
    path('', views.UserListCreateView.as_view(), name='user-list-create'),
    path('<int:user_id>/', views.UserDetailView.as_view(), name='user-detail'),
    path('<int:user_id>/permissions/', views.UserPermissionsView.as_view(), name='user-permissions'),
    path('invite/', InviteClientView.as_view(), name='user-invite'),
    path('accept-invitation/', AcceptInvitationView.as_view(), name='user-accept-invitation'),
]
