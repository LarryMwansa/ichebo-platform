"""
The Handbook's record type and record link registry (DOC F Parts 2.2, 2.5, 3.6).

The single definition. The Handbook workspace, the Governance read-only library
and the sync pull all import from here.
"""

LIBRARY_REFERENCE = 'reference'
LIBRARY_MANDATE = 'mandate'
LIBRARY_KEYS = 'keys'

# Four main categories first, then the three supporting types (DOC F 2.3).
REFERENCE_TYPES = [
    'symbol', 'principle', 'concept', 'divine_pattern',
    'class', 'narrative', 'hrs_framework',
]
MANDATE_TYPES = [
    'mandate', 'statement', 'framework', 'protocol', 'procedure', 'programme',
]
KEY_TYPES = ['key']

GOVERNANCE_TYPES = REFERENCE_TYPES + MANDATE_TYPES

LIBRARY_TYPES = {
    LIBRARY_REFERENCE: REFERENCE_TYPES,
    LIBRARY_MANDATE: MANDATE_TYPES,
    LIBRARY_KEYS: KEY_TYPES,
}

LIBRARY_LABELS = {
    LIBRARY_REFERENCE: 'Reference Library',
    LIBRARY_MANDATE: 'Mandate Library',
    LIBRARY_KEYS: 'Keys Library',
}

REFERENCE_TYPE_LABELS = {
    'symbol':         'Symbols',
    'principle':      'Principles',
    'concept':        'Concepts',
    'divine_pattern': 'Divine Patterns',
    'class':          'Classes',
    'narrative':      'Narratives',
    'hrs_framework':  'HRS Frameworks',
}
MANDATE_TYPE_LABELS = {
    'mandate':   'Mandates',
    'statement': 'Statements',
    'framework': 'Frameworks',
    'protocol':  'Protocols',
    'procedure': 'Procedures',
    'programme': 'Programmes',
}
KEY_TYPE_LABELS = {'key': 'Keys'}

TYPE_LABELS = {**REFERENCE_TYPE_LABELS, **MANDATE_TYPE_LABELS, **KEY_TYPE_LABELS}

TYPE_SINGULAR_LABELS = {
    'symbol':         'Symbol',
    'principle':      'Principle',
    'concept':        'Concept',
    'divine_pattern': 'Divine Pattern',
    'class':          'Class',
    'narrative':      'Narrative',
    'hrs_framework':  'HRS Framework',
    'mandate':        'Mandate',
    'statement':      'Statement',
    'framework':      'Framework',
    'protocol':       'Protocol',
    'procedure':      'Procedure',
    'programme':      'Programme',
    'key':            'Key',
}

# Record links the Handbook may create (DOC F 3.6).
LINK_TYPES = [
    ('part_of',         'Part of'),
    ('derived_from',    'Derived from'),
    ('aligns_with',     'Aligns with'),
    ('authorised_by',   'Authorised by'),
    ('references',      'References'),
    ('has_symbol',      'Has symbol'),
    ('matches_pattern', 'Matches pattern'),
    ('has_subject',     'Has subject'),
    ('has_entity',      'Has entity'),
]
LINK_TYPE_VALUES = {value for value, _ in LINK_TYPES}

# HRS analysis links: a narrative names the records playing each role (DOC F 3.5).
ANALYSIS_LINK_TYPES = {'has_subject', 'has_entity'}


def library_of(record_type):
    """The Library a governance record type belongs to, or None."""
    if record_type in REFERENCE_TYPES:
        return LIBRARY_REFERENCE
    if record_type in MANDATE_TYPES:
        return LIBRARY_MANDATE
    if record_type in KEY_TYPES:
        return LIBRARY_KEYS
    return None
