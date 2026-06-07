## Dependency: django
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt

## Dependency: local
from ..process.lookups._directory import *
from ..models import Shortcut


def shortcut_details(request, shortcut_instance):
    types = shortcut_instance.shortcut_types.split(',')
    if 'ActionExtension' in types:
        _ = shortcut_instance.accepted_types.split(',')
        accepts = ", ".join(_[:-2] + [" and ".join(_[-2:])])
    else:
        accepts = None

    return {
        # Aesthetic Metadata
        'name': shortcut_instance.name,
        'color_code': color_codes.get(shortcut_instance.colorID, '(0,0,0)'),
        'glyph_icon': 'assets/glyphs/' + icon_codes.get(shortcut_instance.glyphID, 'skull.svg'),
        'workflow_version': shortcut_instance.workflow_version,

        # Core Action Dictionaries
        'action_blocks': shortcut_instance.action_blocks['blocks'],
        'UUID_glyphs': shortcut_instance.UUID_glyphs,

        # Functional Metadata
        'iCloud_link': f'https://www.icloud.com/shortcuts/{shortcut_instance.iCloudID}',
        'accepted_types': accepts,
        'types': types,
        'sc_age': reddit_time(timezone.now() - shortcut_instance.created_on),
        'hxid': shortcut_instance.iCloudID,
    }


@xframe_options_exempt
def show_shortcut(request, hxid: str):
    return render(
        request,
        'show_shortcut.html',
        context=shortcut_details(
            request,
            shortcut_instance=get_object_or_404(Shortcut, pk=hxid),
        )
    )


def reddit_time(delta):
    years = int(delta.days / 365)
    months = int(delta.days / 30.5)
    days = delta.days
    hours = int(delta.seconds / 3600)
    mins = int(delta.seconds / 60)
    if   years:  return (f'{years} years'   if years > 1  else 'over a year')
    elif months: return (f'{months} months' if months > 1 else 'a month')
    elif days:   return (f'{days} days'     if days > 1   else 'a day')
    elif hours:  return (f'{hours} hours'   if hours > 1  else 'an hour')
    elif mins:   return (f'{mins} mins'     if mins > 1   else 'just one minute')
    else: return 'mere seconds'
