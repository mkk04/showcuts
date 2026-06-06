## Dependency: boilerplate
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

# views
from share.views import user, misc, submit

urlpatterns = [
    # home page -> submit a Shortcut
    path('', submit.submit_iCloud, name='home'),

    path('admin/', admin.site.urls),

    # Account views (standard username/password auth)
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('settings/', user.users_settings, name='user-settings'),

    path('share/', include('share.urls')),
    path('api/', include('api.urls')),

    # misc static pages
    path('about/', misc.about, name='about'),
    path('wallpaper/', misc.wallpaper, name='wallpaper'),
    path('wallpaper/huge', misc.wallpaper_huge, name='wallpaper-huge'),
]
