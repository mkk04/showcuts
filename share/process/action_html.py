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


def _render(action_cat, WFaction, UUID_glyphs, indent_level):
    sc_action = action_cat(WFaction)
    sc_action.to_django(UUID_glyphs, indent_level)
    return sc_action


def make_html(WFaction_list: [dict]) -> [dict]:
    indent_level = 0
    action_blocks = []
    UUID_glyphs = {} # maps result UUIDs to their respective glyphs

    for WFaction in WFaction_list:
        identifier = WFaction.get('WFWorkflowActionIdentifier', '')
        action_cat = categorize_action(identifier)
        if action_cat is NOT_IMPLEMENTED_ACTION:
            # Fall back to a runtime, user-defined action if one exists.
            action_cat = custom_action_for(identifier) or action_cat

        # Render the action. A single failing action must never take down the
        # whole Shortcut: fall back to the "inferred" placeholder, then to a
        # plain error block, so the rest of the Shortcut still loads.
        sc_action = None
        try:
            sc_action = _render(action_cat, WFaction, UUID_glyphs, indent_level)
        except Exception:
            logging.exception('Failed to render action %r', identifier)
            if settings.DEBUG:
                raise
            try:
                sc_action = _render(NOT_IMPLEMENTED_ACTION, WFaction, UUID_glyphs, indent_level)
            except Exception:
                logging.exception('Inferred fallback also failed for %r', identifier)

        if sc_action is None:
            block = error_action()
            block['identifier'] = identifier
            indent_delta, uuid, glyph = 0, None, ''
        else:
            block = sc_action.__dict__
            indent_delta = sc_action.indent_delta
            uuid = sc_action.UUID
            glyph = sc_action.glyph

        action_blocks.append(block)
        indent_level += indent_delta # update indentation
        UUID_glyphs[uuid] = re.sub('assets/cat/', '', glyph or '') # update UUID glyph dict
    return action_blocks, UUID_glyphs
