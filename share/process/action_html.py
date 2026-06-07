## Dependency: 
import logging, re

# Dependency: django boilerplate
from django.template import engines, TemplateSyntaxError

## Dependency: local
from share.process.sc_action import action
from share.process.sc_action.directory import categorize_action
from share.process.sc_action.custom import build_custom_action
from share.process.lookups._directory import error_action
from share.process.lookups.placeholder import NOT_IMPLEMENTED_ACTION
from django.conf import settings


def custom_action_for(identifier: str):
    '''Look up a user-defined ``CustomAction`` for an unknown identifier.

    Imported lazily to avoid a circular import with ``share.models`` and to
    tolerate the table not existing yet (e.g. before migrations run).
    '''
    try:
        from share.models import CustomAction
        record = CustomAction.objects.filter(identifier=identifier).first()
    except Exception:
        return None
    return build_custom_action(record) if record else None


def make_html(WFaction_list: [dict]) -> [dict]:
    indent_level = 0
    action_blocks = []
    UUID_glyphs = {} # maps result UUIDs to their respective glyphs

    for WFaction in WFaction_list:
        identifier = WFaction['WFWorkflowActionIdentifier']
        action_cat = categorize_action(identifier)
        if action_cat is NOT_IMPLEMENTED_ACTION:
            # Fall back to a runtime, user-defined action if one exists.
            action_cat = custom_action_for(identifier) or action_cat
        try:
            sc_action = action_cat(WFaction) # instantiate chosen class
            sc_action.to_django(UUID_glyphs, indent_level)
        except:
            sc_action = error_action()
            if settings.DEBUG:raise
        action_blocks.append(sc_action.__dict__)
        indent_level += sc_action.indent_delta # update indentation
        UUID_glyphs[sc_action.UUID] = re.sub('assets/cat/','',sc_action.glyph) # update UUID glyph dict
    return action_blocks, UUID_glyphs
