from django.urls import path,include
from.import views

urlpatterns = [
#Hr Pages URl       
    path('',views.login,name='login'),
    path('login',views.login,name='login'),
    path('home',views.home,name='home'),
]