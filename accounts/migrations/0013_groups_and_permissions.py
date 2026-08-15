from django.db import migrations


def create_groups_and_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    def perms(codenames):
        return list(Permission.objects.filter(codename__in=codenames))

    # --- admin: all permissions ---
    admin_group, _ = Group.objects.get_or_create(name='admin')
    all_perms = Permission.objects.all()
    admin_group.permissions.set(all_perms)

    # --- guest ---
    guest_group, _ = Group.objects.get_or_create(name='guest')
    guest_group.permissions.set(perms([
        'view_menu',
        'view_tablelayout',
        'add_cart_user', 'view_cart_user', 'change_cart_user',
        'add_cart_items', 'view_cart_items', 'change_cart_items', 'delete_cart_items',
        'add_order', 'view_order', 'view_orderitem',
        'add_tablereservation', 'view_tablereservation', 'delete_tablereservation',
        'view_customuser',
    ]))

    # --- kitchen ---
    kitchen_group, _ = Group.objects.get_or_create(name='kitchen')
    kitchen_group.permissions.set(perms([
        'view_menu',
        'view_tablelayout',
        'view_order', 'change_order',
        'view_orderitem',
        'add_orderkitchenstaff', 'view_orderkitchenstaff',
        'view_tablereservation',
    ]))

    # --- waiter ---
    waiter_group, _ = Group.objects.get_or_create(name='waiter')
    waiter_group.permissions.set(perms([
        'view_menu',
        'view_tablelayout', 'change_tablelayout',
        'view_cart_user', 'view_cart_items',
        'view_order', 'change_order',
        'view_orderitem',
        'view_orderkitchenstaff',
        'view_tablereservation', 'change_tablereservation',
        'add_tableassign', 'view_tableassign', 'change_tableassign',
        'view_customuser',
    ]))


def remove_groups_and_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['admin', 'guest', 'kitchen', 'waiter']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_table_setup_data'),
        ('auth', '__first__'),
    ]

    operations = [
        migrations.RunPython(create_groups_and_permissions, remove_groups_and_permissions),
    ]
