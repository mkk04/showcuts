"""Web tools: inspect a Shortcut, export it as Markdown for an AI assistant,
and a runtime action generator for adding missing actions."""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from ..models import Shortcut, CustomAction
from ..forms import CustomActionForm, spec_to_text
from ..process.serialize import action_rows, unrecognised, to_markdown


def inspect(request, hxid):
    '''Show every action of a Shortcut with its recognised/unrecognised state.'''
    shortcut = get_object_or_404(Shortcut, pk=hxid)
    rows = action_rows(shortcut)
    return render(request, 'tools/inspect.html', {
        'shortcut': shortcut,
        'rows': rows,
        'missing': unrecognised(rows),
    })


def export_markdown(request, hxid):
    '''Download the Shortcut as a Markdown file (for handing to an AI).'''
    shortcut = get_object_or_404(Shortcut, pk=hxid)
    response = HttpResponse(to_markdown(shortcut), content_type='text/markdown; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{shortcut.iCloudID}.md"'
    return response


@login_required
def rebuild(request, hxid):
    '''Re-fetch the Shortcut from iCloud and re-render it, applying any newly
    added custom actions. Requires network access to iCloud (works on the
    deployed app).'''
    shortcut = get_object_or_404(Shortcut, pk=hxid)
    try:
        from ..process.entry import make_record
        fresh = make_record(shortcut.iCloud, shortcut.owner)
        shortcut.action_blocks = fresh.action_blocks
        shortcut.UUID_glyphs = fresh.UUID_glyphs
        shortcut.save()
        messages.success(request, 'Shortcut rebuilt with the latest actions.')
    except Exception:
        logging.exception('Failed to rebuild shortcut %s', hxid)
        messages.error(request, 'Could not rebuild the Shortcut (iCloud unreachable?).')
    return redirect('inspect', hxid=hxid)


@login_required
def action_list(request):
    '''List all runtime custom actions.'''
    return render(request, 'tools/actions.html', {
        'actions': CustomAction.objects.all(),
    })


@login_required
def action_new(request):
    '''Create or update a custom action.'''
    if request.method == 'POST':
        form = CustomActionForm(request.POST)
        if form.is_valid():
            action = form.save()
            messages.success(request, f'Saved action "{action.name}".')
            return redirect('action-list')
    else:
        form = CustomActionForm(initial={
            'identifier': request.GET.get('identifier', ''),
            'name': request.GET.get('name', ''),
        })
    return render(request, 'tools/action_form.html', {'form': form, 'editing': False})


@login_required
def action_edit(request, pk):
    '''Edit an existing custom action.'''
    instance = get_object_or_404(CustomAction, pk=pk)
    if request.method == 'POST':
        form = CustomActionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Action updated.')
            return redirect('action-list')
    else:
        form = CustomActionForm(initial={
            'identifier': instance.identifier,
            'name': instance.name,
            'category': instance.category,
            'glyph': instance.glyph,
            'result': instance.result,
            'title': spec_to_text(instance.title_spec),
        })
    return render(request, 'tools/action_form.html', {'form': form, 'editing': True})


@login_required
def action_delete(request, pk):
    '''Delete a custom action.'''
    instance = get_object_or_404(CustomAction, pk=pk)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, 'Action deleted.')
    return redirect('action-list')
