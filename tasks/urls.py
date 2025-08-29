from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    TaskListView, TaskDetailView, TaskCreateView,
    TaskUpdateView, TaskDeleteView, toggle_complete, SignupView
)

urlpatterns = [
    # tasks
    path('', TaskListView.as_view(), name='task-list'),
    path('task/new/', TaskCreateView.as_view(), name='task-create'),
    path('task/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('task/<int:pk>/edit/', TaskUpdateView.as_view(), name='task-update'),
    path('task/<int:pk>/delete/', TaskDeleteView.as_view(), name='task-delete'),
    path('task/<int:pk>/toggle/', toggle_complete, name='task-toggle'),

    # authentication
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='tasks/login.html'), name='login'),
path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
