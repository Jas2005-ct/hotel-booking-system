from django.db import migrations


RESTAURANT_SETUP = [
    (2, 4),  # capacity, count
    (4, 3),
    (6, 2),
]

PARTY_SETUP = [
    (8, 2),  # capacity, count
    (10, 2),
    (12, 1),
    (15, 1),
]


def seed_table_setups(apps, schema_editor):
    TableLayout = apps.get_model('accounts', 'TableLayout')
    floor = 1
    counter = TableLayout.objects.order_by('table_no').last()
    start_no = (counter.table_no + 1) if counter else 1
    table_no = start_no

    for capacity, count in RESTAURANT_SETUP:
        for _ in range(count):
            TableLayout.objects.create(
                table_no=table_no, floor_no=floor,
                Location='restaurant', capacity=capacity, available=True
            )
            table_no += 1

    for capacity, count in PARTY_SETUP:
        for _ in range(count):
            TableLayout.objects.create(
                table_no=table_no, floor_no=floor,
                Location='party_setup', capacity=capacity, available=True
            )
            table_no += 1


def unseed_table_setups(apps, schema_editor):
    TableLayout = apps.get_model('accounts', 'TableLayout')
    TableLayout.objects.filter(Location__in=['restaurant', 'party_setup']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0011_alter_tablelayout_location'),
    ]

    operations = [
        migrations.RunPython(seed_table_setups, unseed_table_setups),
    ]
