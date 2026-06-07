"""Renders an Adjust Date ``WFDuration`` ("1 day", "3 months", "[var] weeks").

The duration is stored as a ``WFQuantityFieldValue`` whose ``Value`` holds a
``Magnitude`` (a plain number or a magic variable) and a ``Unit`` (a short code
such as ``days`` or ``hr``). This component renders it defensively, returning
nothing when no duration is set (e.g. the "Get Start of Day" operations).
"""

from ..base_magic import base_magic
from ..magic_helpers import AddField, value_dct, classify_magic

# Shortcuts' short unit codes -> readable labels.
_UNIT_LABELS = {
    'sec': 'seconds', 'secs': 'seconds', 'seconds': 'seconds',
    'min': 'minutes', 'mins': 'minutes', 'minutes': 'minutes',
    'hr': 'hours', 'hrs': 'hours', 'hours': 'hours',
    'day': 'days', 'days': 'days',
    'wk': 'weeks', 'week': 'weeks', 'weeks': 'weeks',
    'mo': 'months', 'month': 'months', 'months': 'months',
    'yr': 'years', 'yrs': 'years', 'year': 'years', 'years': 'years',
}


class duration(base_magic):
    '''Title field for an Adjust Date ``WFDuration`` (magnitude + unit).'''

    def __init__(self, key: str, ask_each_time=None):
        super().__init__(key, ask_each_time, attrs={'key': key})

    @AddField('measurement')
    def to_html(self, params, UUID_glyphs):
        param = params.get(self.key)
        if not isinstance(param, dict):
            if param in (None, ''):
                return []  # no duration (e.g. "Get Start of Day")
            return [value_dct(str(param), attrs=dict(self.attrs))]

        value = param.get('Value') or {}
        out = []
        magnitude_is_one = False

        magnitude = value.get('Magnitude')
        if isinstance(magnitude, dict):
            inner = magnitude.get('Value', magnitude)
            if isinstance(inner, dict) and inner.get('Type'):
                out.append(classify_magic(
                    value=inner, var_type=inner.get('Type'),
                    attrs=dict(self.attrs), UUID_glyphs=UUID_glyphs,
                ))
            elif inner not in (None, ''):
                out.append(value_dct(str(inner), attrs=dict(self.attrs)))
        elif magnitude not in (None, ''):
            out.append(value_dct(str(magnitude), attrs=dict(self.attrs)))
            magnitude_is_one = str(magnitude).strip() == '1'

        unit = value.get('Unit')
        if unit:
            label = _UNIT_LABELS.get(str(unit).lower(), str(unit))
            if magnitude_is_one and label.endswith('s'):
                label = label[:-1]  # "1 day" instead of "1 days"
            out.append(value_dct(label, attrs={}))

        return out
