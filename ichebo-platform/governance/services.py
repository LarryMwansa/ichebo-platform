# governance/services.py — query helpers and transaction functions
from django.db import transaction
from django.utils import timezone

from records.models import Record, Relationship


# ── Record type groups (v10 authority matrix, Part 15.2) ──────────────────────
#
# Reference Library — Level 3+ read, Level 5 write, Handbook tenant only
LIBRARY_TYPES = [
    'class', 'principle', 'concept', 'divine_pattern',
]

# Mandate Branch — Level 4+ read, Level 5 write, Handbook tenant only
MANDATE_TYPES = [
    'mandate', 'statement', 'framework', 'narrative',
    'subject', 'entity', 'protocol', 'procedure', 'programme',
]

LIBRARY_TYPE_LABELS = {
    'class':          'Classes',
    'principle':      'Principles',
    'concept':        'Concepts',
    'divine_pattern': 'Divine Patterns',
}

MANDATE_TYPE_LABELS = {
    'mandate':   'Mandates',
    'statement': 'Statements',
    'framework': 'Frameworks',
    'narrative': 'Narratives',
    'subject':   'Subjects',
    'entity':    'Entities',
    'protocol':  'Protocols',
    'procedure': 'Procedures',
    'programme': 'Programmes',
}

HRS_COMPLEXITY_CHOICES = ['Low', 'Medium', 'High', 'Transcendent']
HRS_POLARITY_CHOICES   = ['subjective', 'objective']
HRS_POSITION_CHOICES   = ['up', 'down', 'left', 'right']
HRS_DIRECTION_CHOICES  = ['forward', 'backward']
HRS_SPEED_CHOICES      = ['fast', 'slow']

# v10 relationship types for Governance App (Part 3.4 — has_subject/has_entity removed)
RELATIONSHIP_TYPES = [
    'part_of', 'derived_from', 'aligns_with', 'authorised_by',
    'references', 'tracks', 'community_ref',
]


def get_handbook_records(record_type, search='', status_filter=None):
    """Returns QS of governance records of a given type."""
    qs = Record.objects.filter(
        record_family='governance',
        record_type=record_type,
        deleted_at__isnull=True,
    ).order_by('-created_at')

    if search:
        qs = qs.filter(title__icontains=search)

    if status_filter:
        qs = qs.filter(status=status_filter)
    else:
        qs = qs.exclude(status='superseded')

    return qs


def get_key_records(user, search=''):
    """Returns Key Records created by this user."""
    qs = Record.objects.filter(
        record_family='reference',
        record_type='key',
        created_by=user,
        deleted_at__isnull=True,
    ).order_by('-created_at')

    if search:
        qs = qs.filter(title__icontains=search)

    return qs


def get_version_chain(record):
    """
    Traverse previous_version chain backward to find oldest,
    then build forward to current. Returns ordered list v1 → current.
    """
    chain = [record]

    # Walk backward to root
    current = record
    seen = {current.id}
    while current.previous_version_id:
        try:
            current = Record.objects.get(id=current.previous_version_id)
        except Record.DoesNotExist:
            break
        if current.id in seen:
            break
        seen.add(current.id)
        chain.insert(0, current)

    return chain


def get_linked_records(record_id):
    """Returns all Relationship rows for a record, grouped by type."""
    outgoing = (
        Relationship.objects
        .filter(from_record_id=record_id, deleted_at__isnull=True)
        .select_related('to_record', 'bible_verse',
                       'bible_verse__book')
    )
    incoming = (
        Relationship.objects
        .filter(to_record_id=record_id, deleted_at__isnull=True)
        .select_related('from_record', 'bible_verse', 'bible_verse__book')
    )

    grouped = {}
    for rel in outgoing:
        grouped.setdefault(rel.relationship_type, []).append({
            'direction': 'out',
            'rel': rel,
            'record': rel.to_record,
            'bible_verse': rel.bible_verse,
        })
    for rel in incoming:
        grouped.setdefault(rel.relationship_type, []).append({
            'direction': 'in',
            'rel': rel,
            'record': rel.from_record,
            'bible_verse': rel.bible_verse,
        })

    return grouped


def create_new_version(old_record, user):
    """
    Atomic supersede flow:
    1. Create new draft with previous_version = old_record
    2. Patch old record: status='superseded', superseded_by=new
    Returns new record.
    """
    with transaction.atomic():
        new_version_num = (old_record.version or 1) + 1

        new_record = Record.objects.create(
            created_by=user,
            record_class=old_record.record_class,
            record_family=old_record.record_family,
            record_type=old_record.record_type,
            origin=old_record.origin or 'user',
            title=old_record.title,
            content=old_record.content,
            summary=old_record.summary,
            status='draft',
            version=new_version_num,
            previous_version=old_record,
            tags=list(old_record.tags or []),
            categories=list(old_record.categories or []),
            custom_fields=dict(old_record.custom_fields or {}),
            metadata={'source_app': 'governance'},
            permissions_data=dict(old_record.permissions_data or {}),
            tenant=old_record.tenant,
        )

        old_record.status = 'superseded'
        old_record.superseded_by = new_record
        old_record.save(update_fields=['status', 'superseded_by', 'updated_at'])

    return new_record
