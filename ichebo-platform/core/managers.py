"""
Soft-delete manager and abstract mixin for all syncable Ichebo models.

Phase E.2 — every syncable entity carries a deleted_at field and uses
SoftDeleteManager as its default objects manager so that all ORM queries
automatically exclude deleted rows without needing manual filter calls.

Usage:
    class MyModel(SoftDeleteMixin, models.Model):
        ...

Hard-delete is intentionally not provided. The only delete path is
obj.soft_delete() which sets deleted_at to now. The row is never removed.

Exempt models (read-only seed data, no write path through the engine layer):
    BibleTranslation, BibleBook, BibleVerse, ParacletePrompt, SyncChangelog
"""

from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet that adds a .soft_delete() bulk method."""

    def soft_delete(self):
        return self.update(deleted_at=timezone.now())

    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager):
    """
    Default manager — automatically excludes soft-deleted rows.
    Use Model.all_objects.all() to include deleted rows.
    """

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(
            deleted_at__isnull=True
        )

    def soft_delete(self):
        return self.get_queryset().soft_delete()


class AllObjectsManager(models.Manager):
    """
    Unfiltered manager — includes soft-deleted rows.
    Accessed via Model.all_objects.
    Used by: sync pull (must see deleted entities to propagate deletes),
    admin panels, audit views.
    """

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteMixin(models.Model):
    """
    Abstract mixin that wires up soft-delete behaviour.

    Adds:
        deleted_at      — null = alive, timestamp = deleted
        objects         — SoftDeleteManager (default, excludes deleted)
        all_objects     — AllObjectsManager (includes deleted, for sync/admin)

    Provides:
        soft_delete()   — sets deleted_at = now(), saves
        restore()       — clears deleted_at, saves
        is_deleted      — bool property
    """

    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
