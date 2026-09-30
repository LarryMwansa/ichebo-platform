"""
Who may read what in the Handbook (DOC F Parts 5.1, 6.1, 6.2).

The single definition of the read rules, shared by the Handbook workspace and
the Governance read-only library.
"""
from records.models import Record

from .models import HandbookAccess
from .registry import MANDATE_TYPES

REFERENCE_ACCESS_LEVEL = 3
MANDATE_ACCESS_LEVEL = 4
KEYS_ACCESS_LEVEL = 3

PUBLISHED_STATUSES = ('active', 'locked')


def level(user):
    return getattr(user, 'competence_level', 0)


def get_access(user):
    return HandbookAccess.objects.filter(user=user).first()


def can_write(access):
    return bool(access) and access.role in (HandbookAccess.ROLE_AUTHOR, HandbookAccess.ROLE_EDITOR)


def is_editor(access):
    return bool(access) and access.role == HandbookAccess.ROLE_EDITOR


def _sees_everything(user, access):
    return user.is_superuser or user.is_staff or can_write(access)


def governance_qs(user, access, include_drafts=False):
    """Governance records this user may read: Reference from Level 3, Mandate from Level 4."""
    qs = Record.objects.filter(
        record_family='governance',
        deleted_at__isnull=True,
    ).exclude(record_type='key')

    if _sees_everything(user, access):
        return qs
    if level(user) < REFERENCE_ACCESS_LEVEL:
        return qs.none()
    if level(user) < MANDATE_ACCESS_LEVEL:
        qs = qs.exclude(record_type__in=MANDATE_TYPES)
    if include_drafts:
        return qs
    return qs.filter(status__in=PUBLISHED_STATUSES)


def can_see_record(user, access, record):
    """Whether one record may be shown to this user.

    Personal records (journals, keys, notes) are visible to their owner only — not to
    authors, editors or superusers. Governance records follow governance_qs.
    """
    if record.created_by_id == user.pk:
        return True
    if record.record_family != 'governance' or record.record_type == 'key':
        return False
    if _sees_everything(user, access):
        return True
    if level(user) < REFERENCE_ACCESS_LEVEL:
        return False
    if level(user) < MANDATE_ACCESS_LEVEL and record.record_type in MANDATE_TYPES:
        return False
    return bool(access) or record.status in PUBLISHED_STATUSES


def has_journal_link(record):
    """A record published to the network must not carry a link to a journal entry (DOC F 6.2)."""
    return (
        record.outgoing_relationships.filter(to_record__record_family='journal', deleted_at__isnull=True).exists()
        or record.incoming_relationships.filter(from_record__record_family='journal', deleted_at__isnull=True).exists()
    )
