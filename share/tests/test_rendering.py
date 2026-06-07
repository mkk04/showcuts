"""Offline tests for the action rendering pipeline (no network required)."""

from django.test import TestCase

from share.process.action_html import make_html


def _act(identifier, **params):
    return {'WFWorkflowActionIdentifier': identifier,
            'WFWorkflowActionParameters': params}


def _titles(blocks):
    out = []
    for b in blocks:
        text = ' '.join(
            str(e.get('value', '')) for e in b.get('title', [])
            if isinstance(e, dict) and isinstance(e.get('value'), str)
        ).strip()
        out.append(text)
    return out


def _inferred(block):
    return 'inferred' in (block.get('css_class') or [])


class RenderingTest(TestCase):

    def test_choose_from_menu(self):
        blocks, _ = make_html([
            _act('is.workflow.actions.choosefrommenu', WFControlFlowMode=0, WFMenuPrompt='Pick'),
            _act('is.workflow.actions.choosefrommenu', WFControlFlowMode=1, WFMenuItemTitle='MNP'),
            _act('is.workflow.actions.gettext'),
            _act('is.workflow.actions.choosefrommenu', WFControlFlowMode=2),
        ])
        titles = _titles(blocks)
        self.assertEqual(titles[0], 'Choose from Menu Pick')
        self.assertEqual(titles[1], 'Case MNP')
        self.assertEqual(titles[3], 'End Menu')
        self.assertEqual(blocks[2]['indent'], 1)  # content indented under the case

    def test_if_head_is_robust_and_keeps_indentation(self):
        # An ActionOutput input without OutputName previously made the If head
        # raise, falling back to "inferred" and corrupting all following indents.
        bad = {'Value': {'Type': 'ActionOutput', 'OutputUUID': 'U'},
               'WFSerializationType': 'WFTextTokenAttachment'}
        blocks, _ = make_html([
            _act('is.workflow.actions.conditional', WFControlFlowMode=0, WFInput=bad, WFCondition=100),
            _act('is.workflow.actions.gettext'),
            _act('is.workflow.actions.conditional', WFControlFlowMode=2),
            _act('is.workflow.actions.gettext'),
        ])
        self.assertFalse(_inferred(blocks[0]))
        self.assertTrue(_titles(blocks)[0].startswith('If'))
        self.assertEqual(blocks[1]['indent'], 1)   # inside the If
        self.assertEqual(blocks[3]['indent'], 0)   # back to baseline after End If

    def test_newly_added_actions_are_recognised(self):
        for ident in ['takephoto', 'selectphoto', 'addnewreminder', 'setters.reminders']:
            blocks, _ = make_html([_act('is.workflow.actions.' + ident)])
            self.assertFalse(_inferred(blocks[0]), f'{ident} should be recognised')

    def test_title_less_action_falls_back_to_name(self):
        blocks, _ = make_html([_act('is.workflow.actions.format.date')])
        self.assertEqual(_titles(blocks)[0], 'Format Date')
