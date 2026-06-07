## Dependency: django
from django.test import TestCase
from django.urls import reverse

## Dependency: shortcut to populate
from share.models import Shortcut

pk='ffffffffffffffffffffffffffffffff'

class submit_iCloud_Test(TestCase):
    @classmethod
    def setUpTestData(cls):
        Shortcut.objects.create(
            iCloud='https://www.icloud.com/shortcuts/' + pk,
            iCloudID=pk,
            download_link='https://cvws.icloud-content.com/B/AUfAj59DvD5fAY8RNlW1SM3lTout/b96b5b1801994aa08c2e8cd064b69f6e?o=AkipWEjlm_5djNcnXYYadmaf8C1QFgWPCdDpUD5LB3WTfVlkajaE_KbckKaatDx5AA&v=1&x=3&a=CAxgR8Zmn-R_qDQOkcuutplE0lViyaD9LGfMEK_xyLkEAd8SFxC_2dyP6C0Yv7a4kegtIgEAUgTlTout&e=1574142090&k=_&fl=&r=88b6ca3c-26ea-4e6e-8808-48c7646a8f19-1&ckc=com.apple.shortcuts&ckz=_defaultZone&p=33&s=kBbWxP0bSEIJgtojb3q-x1cw7lw',
            action_blocks={'blocks':[]}, 
            UUID_glyphs={},
            #TODO accept categories later
            #TODO accept tags later
            name='Test Shortcut',
            glyphID=0,
            colorID=0,
        )

    def test_submit_locations(self):
        response = self.client.get('/share/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/share') # redirects
        self.assertTrue(response.status_code in [200, 301])
        response = self.client.get('/share/submit')
        self.assertTrue(response.status_code in [200, 301])
        response = self.client.get('/share/view')
        self.assertEqual(response.status_code, 200)

    def test_submit_reverse(self):
        response = self.client.get(reverse('submit'))

    def test_view_locations(self):
        response = self.client.get('/share/view/'+pk)
        self.assertEqual(response.status_code, 200)

    def test_view_reverse(self):
        response = self.client.get(reverse('view',kwargs={'hxid':pk}))


class PublicPagesTest(TestCase):
    '''Core public pages render without any authentication.'''

    def test_home_page_renders(self):
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)

    def test_about_page_renders(self):
        self.assertEqual(self.client.get(reverse('about')).status_code, 200)

    def test_action_generator_is_public(self):
        self.assertEqual(self.client.get(reverse('action-new')).status_code, 200)
        self.assertEqual(self.client.get(reverse('action-list')).status_code, 200)


class ToolsTest(TestCase):
    '''Inspect page, Markdown export and the runtime action generator.'''

    hx = 'c' * 32

    @classmethod
    def setUpTestData(cls):
        from share.process.action_html import make_html
        raw = [
            {'WFWorkflowActionIdentifier': 'is.workflow.actions.comment',
             'WFWorkflowActionParameters': {'WFCommentActionText': 'hi'}},
            {'WFWorkflowActionIdentifier': 'is.workflow.actions.totallyunknownxyz',
             'WFWorkflowActionParameters': {'WFFoo': 'bar'}},
        ]
        blocks, glyphs = make_html(raw)
        Shortcut.objects.create(
            iCloud='https://www.icloud.com/shortcuts/' + cls.hx, iCloudID=cls.hx,
            download_link='https://x', action_blocks={'blocks': blocks},
            UUID_glyphs=glyphs, name='Demo', glyphID=0, colorID=0,
        )

    def test_inspect_lists_unrecognised(self):
        response = self.client.get(reverse('inspect', kwargs={'hxid': self.hx}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'is.workflow.actions.totallyunknownxyz')

    def test_markdown_export(self):
        response = self.client.get(reverse('export-md', kwargs={'hxid': self.hx}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/markdown', response['Content-Type'])
        self.assertIn('is.workflow.actions.totallyunknownxyz', response.content.decode())

    def test_custom_action_created_via_form(self):
        response = self.client.post(reverse('action-new'), {
            'identifier': 'is.workflow.actions.totallyunknownxyz',
            'name': 'Do XYZ', 'category': 'WEB', 'glyph': 'Web.svg', 'result': '',
            'title': 'text: Do XYZ with\nmagic: WFFoo | Foo',
        })
        self.assertEqual(response.status_code, 302)  # redirect on success, no login
        from share.models import CustomAction
        self.assertTrue(CustomAction.objects.filter(
            identifier='is.workflow.actions.totallyunknownxyz').exists())

    def test_custom_action_is_applied(self):
        from share.models import CustomAction
        from share.process.action_html import make_html

        CustomAction.objects.create(
            identifier='is.workflow.actions.totallyunknownxyz',
            name='Do XYZ', category='WEB', glyph='Web.svg',
            title_spec=[{'type': 'text', 'value': 'Do XYZ with'},
                        {'type': 'magic', 'key': 'WFFoo', 'blank': 'Foo'}],
        )
        blocks, _ = make_html([
            {'WFWorkflowActionIdentifier': 'is.workflow.actions.totallyunknownxyz',
             'WFWorkflowActionParameters': {'WFFoo': 'bar'}}])
        self.assertEqual(blocks[0]['category'], 'WEB')
        self.assertNotIn('inferred', blocks[0].get('css_class') or [])

