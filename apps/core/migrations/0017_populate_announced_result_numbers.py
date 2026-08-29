from django.db import migrations

def populate_result_numbers(apps, schema_editor):
    Program = apps.get_model('core', 'Program')
    Competition = apps.get_model('core', 'Competition')

    for comp in Competition.objects.all():
        announced_progs = list(Program.objects.filter(competition=comp, is_announced=True).order_by('announced_at', 'id'))
        seq = 1
        for prog in announced_progs:
            if not prog.result_number:
                prog.result_number = seq
                prog.save(update_fields=['result_number'])
            seq += 1

def reverse_func(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_program_result_number'),
    ]

    operations = [
        migrations.RunPython(populate_result_numbers, reverse_func),
    ]
