import share.process.sc_action.action as action
from share.process.lookups.infer import infer_action
infoless = {'glyph': 'Missing.svg', 'category': 'MISSING'}

def error_action():
    return {
        'title': [{'value':'Error Loading Action','class':'error'}],
        'line': [],
        'glyph': '',#deliberately blank
        'category': '',
        'indent': '',
    }

class NOT_IMPLEMENTED_ACTION(action.action):
    '''Fallback for actions without a hand-coded definition.

    Instead of a generic placeholder, the action's identifier is parsed into
    a best-effort name/category/glyph so newly-released or third-party actions
    are still recognised at a basic level.
    '''
    def modify(self):
        info = infer_action(getattr(self, 'identifier', ''))
        self.name = info['name']
        self.title = [{
            'value':info['name'],
            'class':['inferred'],
            'attrs':{
                'key':None,
                'identifier':info['identifier'],
            },
        }]
        self.glyph = f"assets/cat/{info['glyph']}"
        self.category = info['category']
        self.css_class = ['inferred']

def not_implemented_options():
    return {
        'label':'',
        'class':'not-implemented',
        'value':'Options Under Construction',
    }