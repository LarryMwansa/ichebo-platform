from django.apps import AppConfig
from django.core.checks import Error, register


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        register(check_uuid_primary_keys)


@register()
def check_uuid_primary_keys(app_configs, **kwargs):
    """
    System check: every model in the platform must use UUIDField as its
    primary key. BigAutoField integer PKs are not compatible with the Sync
    Engine — records created offline must have permanent identities before
    reaching the cloud.

    Exemptions (seed/reference data models with no sync requirement):
      - django.contrib.* internal models
      - django_token_auth and DRF Token models
    """
    from django.apps import apps
    import uuid

    EXEMPT_APP_LABELS = {
        'admin', 'auth', 'contenttypes', 'sessions',
        'authtoken',  # DRF token
    }

    errors = []
    for model in apps.get_models():
        app_label = model._meta.app_label
        if app_label in EXEMPT_APP_LABELS:
            continue
        pk = model._meta.pk
        if pk is None:
            continue
        from django.db.models import UUIDField, OneToOneField
        if not isinstance(pk, (UUIDField, OneToOneField)):
            errors.append(
                Error(
                    f'{model.__name__} uses a non-UUID primary key ({type(pk).__name__}). '
                    f'All platform models must use UUIDField(primary_key=True) '
                    f'for Sync Engine compatibility.',
                    obj=model,
                    id='core.E001',
                )
            )
    return errors
