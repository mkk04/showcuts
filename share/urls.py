from django.urls import path
from share.views import submit, misc, display, tools

urlpatterns = [
    # aliases for home view
    path('', submit.submit_iCloud, name='submit'),
    path('submit/', submit.submit_iCloud, name='submit'),
    path('view', submit.submit_iCloud, name='submit'),
    path('view/<str:hxid>', display.show_shortcut, name='view'),

    # tools: inspect, export, rebuild
    path('view/<str:hxid>/inspect', tools.inspect, name='inspect'),
    path('view/<str:hxid>/export.md', tools.export_markdown, name='export-md'),
    path('view/<str:hxid>/rebuild', tools.rebuild, name='rebuild'),

    # runtime action generator (no login)
    path('actions/', tools.action_list, name='action-list'),
    path('actions/new', tools.action_new, name='action-new'),
    path('actions/<int:pk>/edit', tools.action_edit, name='action-edit'),
    path('actions/<int:pk>/delete', tools.action_delete, name='action-delete'),

    # misc paths
    path('error/', misc.error, name='error'),
]
