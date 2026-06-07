## Dependency: boilerplate
from django.urls import path, include

# views
from share.views import misc, submit

urlpatterns = [
    # home page -> submit a Shortcut
    path('', submit.submit_iCloud, name='home'),

    path('share/', include('share.urls')),
    path('api/', include('api.urls')),

    # misc static pages
    path('about/', misc.about, name='about'),
    path('wallpaper/', misc.wallpaper, name='wallpaper'),
    path('wallpaper/huge', misc.wallpaper_huge, name='wallpaper-huge'),
]
