## Dependency: sys
from datetime import datetime

# boilerplate
from django.db import models

# JSONField
from django.core.serializers.json import DjangoJSONEncoder
import json
from share.process.sc_action.action import action

# serializer
from share.process.lookups._directory import color_codes, icon_codes


def byt_catcher(o):
    if isinstance(o, datetime):
        return o.__str__()
    else:
        return o.decode('UTF-8')

class JSONField(models.TextField):
    def to_python(self, value):
        if value == "":
            return None
        try:
            if isinstance(value, str):
                return json.loads(value, object_hook=action.action_hook)
        except ValueError:
            pass
        return value

    def from_db_value(self, value, *args):
        return self.to_python(value)

    def get_db_prep_save(self, value, *args, **kwargs):
        if value == "":
            return None
        if isinstance(value, dict):
            value = json.dumps(value, cls=DjangoJSONEncoder, default=byt_catcher)
        return value

class Shortcut(models.Model):
    '''represents an iOS Siri Shortcut'''
    iCloud = models.URLField(
        'iCloud link',
        'iCloud',
        max_length=100, # should be ~65 chars
        help_text='iCloud link created by Sharing your Shortcut'
    )
    iCloudID = models.CharField(
        'iCloud ID',
        max_length = 50, # should be 32 Hexadecimal chars
        primary_key=True,
    )
    # credit: insideGUI
    # https://github.com/sharecuts/website/blob/master/Docs/Download%20shortcut%20shared%20as%20a%20link.txt
    download_link = models.URLField(
        'Download Link',
        'download_link',
        max_length=600, # ~400 chars, need to include Auth info
    )
    action_blocks = JSONField(
        'Shortcut Actions',
        'action_blocks',
        default=dict,
    )
    UUID_glyphs = JSONField(
        'UUID Glyphs',
        'UUID_glyphs',
        default=dict,
    )
    name = models.CharField(
        'Name',
        max_length=100,
    )
    glyphID = models.PositiveIntegerField(
        'Glyph ID',
        default=59771, # magic wand glyph
    )
    colorID = models.PositiveIntegerField(
        'Color ID',
        default=431817727, # some valid color
    )
    workflow_version = models.IntegerField(
        'Workflow Version',
        default=0,
    )
    shortcut_types = models.CharField(
        'Shortcut Types',
        'shortcut_types',
        max_length=200,
        default='',
    )
    accepted_types = models.CharField(
        'Accepts',
        'accepted_types',
        max_length=1000, # there are a lot of possible inputs, typical length ~600char
        default='',
    )
    created_on = models.DateTimeField(
        'Created On',
        'created_on',
        auto_now=False,
        auto_now_add=True,
    )
    def __str__(self):
        return f'{self.name}, ID {self.iCloudID}'

    def get_absolute_url(self):
        # URL is linked to hexademical ID, nothing needed here
        pass
    
    def get_actions(self):
        return [i.__dict__ for i in self.action_blocks['blocks']]

    def get_icon(self):
        return {
            'colorID':self.colorID,
            'glyphID':self.glyphID,
        }

    class Meta:
        ordering = ['-created_on']

class CustomAction(models.Model):
    '''A user-defined rendering for a Shortcut action identifier.

    Lets the action generator add support for missing actions at runtime
    (stored in the database) without changing code or redeploying.
    '''
    identifier = models.CharField(
        'Action Identifier',
        max_length=200,
        unique=True,
        help_text='Full identifier, e.g. is.workflow.actions.something',
    )
    name = models.CharField('Name', max_length=100)
    category = models.CharField('Category', max_length=50, default='SHORTCUTS')
    glyph = models.CharField(
        'Glyph file', max_length=60, default='Magic.svg',
        help_text='A file name from staticfiles/assets/cat/, e.g. Web.svg',
    )
    result = models.CharField(
        'Result name', max_length=100, blank=True, default='',
        help_text='What the action outputs, if anything (leave blank for none).',
    )
    # List of title segments. Each item is one of:
    #   {"type": "text",   "value": "Set foo to"}
    #   {"type": "magic",  "key": "WFInput",  "blank": "Input"}
    #   {"type": "inline", "key": "WFText",   "blank": "Text"}
    title_spec = models.JSONField('Title segments', default=list, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['identifier']

    def __str__(self):
        return f'{self.name} ({self.identifier})'