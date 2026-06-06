## Dependency: sys
import re

# Dependency: django boilerplate
from django import forms
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as ug

## Dependency: local
from share.process.entry import api_request


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
