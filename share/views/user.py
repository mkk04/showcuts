## Dependency: django
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

## Dependency: local
from ..models import Shortcut

class users_saved(LoginRequiredMixin, ListView):
    model = Shortcut
    template_name = 'user/saved.html'
    paginate_by = 20

    def get_queryset(self):
        return self.request.user.liked.all()
        # TODO: add sorting options? default: date submitted

class users_liked(LoginRequiredMixin, ListView):
    model = Shortcut
    template_name = 'user/liked.html'
    paginate_by = 20

    def get_queryset(self):
        return self.request.user.saved.all()
        # TODO: add sorting options? default: date saved

class users_submitted(LoginRequiredMixin, ListView):
    model = Shortcut
    template_name = 'user/submitted.html'
    paginate_by = 20

    def get_queryset(self):
        return Shortcut.objects.filter(owner=self.request.user)
        # TODO: add sorting options?

@login_required
def users_settings(request):
    return render(request, 'user/settings.html', {
        'user': request.user,
    })