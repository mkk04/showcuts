## Dependency: sys
import re

# Dependency: django boilerplate
from django import forms
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as ug

## Dependency: local
from share.process.entry import api_request
from share.models import CustomAction


class iCloudForm(forms.Form):

    iCloudLink = forms.CharField(
        help_text="Enter an Shortcut iCloud link",
        widget=forms.TextInput(attrs={'placeholder': 'Shortcut iCloud link'})
    )

    def clean_iCloudLink(self):
        url = self.cleaned_data['iCloudLink']

        try:
            _id = re.findall(r'/([0-9a-f]{32})$', url)[0]
        except IndexError:
            try:
                _id = re.findall(r'^([0-9a-f]{32})$', url)[0]
            except IndexError:
                raise ValidationError(ug('Link doesn\'t contain a valid Shortcut ID'))

        response = api_request(
            u'https://www.icloud.com/shortcuts/api/records/'+_id)
        if response.get('error', None):
            raise ValidationError(ug('Unable to find Shortcut'))

        return url


def parse_title_spec(text: str) -> list:
    '''Parse the friendly title syntax into a ``title_spec`` list.

    One segment per line:
        text: Set foo to        -> static label (the "text:" prefix is optional)
        magic: WFInput | Input   -> variable field (key | placeholder)
        inline: WFText | Text    -> text-with-variables field
    '''
    spec = []
    for raw in (text or '').splitlines():
        line = raw.strip()
        if not line:
            continue
        kind, _, rest = line.partition(':')
        kind = kind.strip().lower()
        rest = rest.strip()
        if kind in ('magic', 'field', 'inline'):
            key, _, blank = rest.partition('|')
            seg = {'type': 'magic' if kind == 'field' else kind, 'key': key.strip()}
            if blank.strip():
                seg['blank'] = blank.strip()
            spec.append(seg)
        elif kind == 'text':
            spec.append({'type': 'text', 'value': rest})
        else:
            spec.append({'type': 'text', 'value': line})
    return spec


def spec_to_text(spec: list) -> str:
    '''Inverse of ``parse_title_spec`` — for pre-filling the edit form.'''
    lines = []
    for seg in (spec or []):
        kind = seg.get('type')
        if kind == 'text':
            lines.append(f"text: {seg.get('value', '')}")
        else:
            line = f"{kind}: {seg.get('key', '')}"
            if seg.get('blank'):
                line += f" | {seg['blank']}"
            lines.append(line)
    return '\n'.join(lines)


class CustomActionForm(forms.Form):
    '''Friendly form for the runtime action generator.'''

    identifier = forms.CharField(
        label='Action identifier',
        widget=forms.TextInput(attrs={'placeholder': 'is.workflow.actions.something'}),
    )
    name = forms.CharField(
        label='Display name',
        widget=forms.TextInput(attrs={'placeholder': 'Do Something'}),
    )
    category = forms.CharField(initial='SHORTCUTS', required=False)
    glyph = forms.CharField(
        initial='Magic.svg', required=False,
        help_text='A file from staticfiles/assets/cat/, e.g. Web.svg',
    )
    result = forms.CharField(
        required=False,
        help_text='Output name, if the action produces one (else leave blank).',
    )
    title = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder':
            'text: Do something with\nmagic: WFInput | Input'}),
        help_text='One title segment per line. See the examples above the box.',
    )

    def clean_identifier(self):
        return self.cleaned_data['identifier'].strip()

    def save(self) -> CustomAction:
        data = self.cleaned_data
        action, _ = CustomAction.objects.update_or_create(
            identifier=data['identifier'],
            defaults={
                'name': data['name'],
                'category': (data.get('category') or 'SHORTCUTS').strip() or 'SHORTCUTS',
                'glyph': (data.get('glyph') or 'Magic.svg').strip() or 'Magic.svg',
                'result': data.get('result') or '',
                'title_spec': parse_title_spec(data.get('title', '')),
            },
        )
        return action
