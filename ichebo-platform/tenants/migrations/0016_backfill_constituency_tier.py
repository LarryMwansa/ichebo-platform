from django.db import migrations


def forwards(apps, schema_editor):
    """Split the old overloaded 'local' tier into its two real meanings:
    a Metro (direct child of a Province, no Constituency layer beneath it)
    becomes 'district' — the same tier an ordinary District Municipality
    already uses; a genuine Local Municipality (child of a District) becomes
    'constituency'. See the TIER_CHOICES comment on tenants.models.Tenant
    for why these were unified in the first place and why they're being
    split back out now to match the canonical country-agnostic geographic
    tree (Continent > Region > Country > Province > District > Constituency
    > Ward).
    """
    Tenant = apps.get_model('tenants', 'Tenant')
    local_tier = Tenant.objects.filter(tier='local')

    metros = local_tier.filter(parent__tier='provincial')
    metro_count = metros.update(tier='district')

    municipalities = Tenant.objects.filter(tier='local', parent__tier='district')
    municipality_count = municipalities.update(tier='constituency')

    remainder = Tenant.objects.filter(tier='local').count()
    if remainder:
        raise RuntimeError(
            f"{remainder} tenant(s) still have tier='local' after the "
            f"metro/municipality split — their parent isn't 'provincial' or "
            f"'district' as expected. Investigate before re-running; this "
            f"migration intentionally refuses to guess for unexpected shapes."
        )

    print(f"\n  Migrated {metro_count} metro(s) 'local' -> 'district'")
    print(f"  Migrated {municipality_count} local municipalit(y/ies) 'local' -> 'constituency'")


def backwards(apps, schema_editor):
    """Not reversible in a lossless way — a 'district' tenant with children
    that were re-tiered as 'constituency' can't be told apart from a
    District Municipality that was always 'district'. Refuse rather than
    silently corrupt data on a rollback.
    """
    raise RuntimeError(
        "0016_backfill_constituency_tier is not reversible — the split "
        "between genuine District Municipalities and migrated Metros can no "
        "longer be distinguished once merged into 'district'. Restore from "
        "a backup instead of reverse-migrating."
    )


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0015_alter_tenant_tier'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
