from django.urls import path
from share.views import submit, misc, display, user, collections, tools

urlpatterns = [
    # aliases for home view
    path('', submit.submit_iCloud, name='submit'),
    path('submit/', submit.submit_iCloud, name='submit'),
    path('view', submit.submit_iCloud, name='submit'),# could later become a browsing page
    path('view/<str:hxid>',display.show_shortcut, name='view'),

    # tools: inspect, export, rebuild
    path('view/<str:hxid>/inspect', tools.inspect, name='inspect'),
    path('view/<str:hxid>/export.md', tools.export_markdown, name='export-md'),
    path('view/<str:hxid>/rebuild', tools.rebuild, name='rebuild'),

    # runtime action generator
    path('actions/', tools.action_list, name='action-list'),
    path('actions/new', tools.action_new, name='action-new'),
    path('actions/<int:pk>/edit', tools.action_edit, name='action-edit'),
    path('actions/<int:pk>/delete', tools.action_delete, name='action-delete'),

    # for logged in users
    path('submitted/', user.users_submitted.as_view(), name='user-submitted'),
    path('liked/', user.users_liked.as_view(), name='user-liked'),
    path('saved/', user.users_saved.as_view(), name='user-saved'),

    # gallery views
    path('gallery/', collections.gallery, name='coll-gallery'),

    # misc paths
    path('error/', misc.error, name='error'),

    # AJAX paths
    path('like/', display.like_shortcut, name='like-shortcut'),
    path('save/', display.save_shortcut, name='save-shortcut'),
    path('premium/', display.grant_premium, name='grant-premium'),
]