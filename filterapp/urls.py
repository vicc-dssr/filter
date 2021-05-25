from django.conf.urls import url
from django.urls import path
from filterapp import views


urlpatterns = [
    path('patients/', views.PatientList.as_view()),
    path('patients/<int:pk>/', views.PatientDetail.as_view()),
    path('users/', views.UserList.as_view()),
    path('users/<int:pk>/', views.UserDetail.as_view()),
    path('games/', views.GameList.as_view()),
    path('games/<int:pk>/', views.GameDetail.as_view()),
    path('actions/', views.UserGameActionList.as_view()),
    path('actions/<int:pk>/', views.UserGameActionDetail.as_view()),
    path('domains/', views.DomainList.as_view()),
    path('institutions/', views.InstitutionList.as_view()),
    path('patient/generate', views.gen_patient),
    path('game/init', views.init_game_board),
    path('game/generate/<int:user_id>', views.gen_game2),
    path('game/count/<int:user_id>', views.games_cnt_by_user),
    path('game/count', views.games_cnt),
    url(r"^register/", views.register, name="register"),
]
