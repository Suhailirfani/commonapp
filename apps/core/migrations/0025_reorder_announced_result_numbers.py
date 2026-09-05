from django.db import migrations
from django.utils import timezone

def reorder_announced_results(apps, schema_editor):
    Program = apps.get_model('core', 'Program')
    Competition = apps.get_model('core', 'Competition')

    for comp in Competition.objects.all():
        # Clear result_number from unannounced programs
        Program.objects.filter(competition=comp, is_announced=False).update(result_number=None)

        # Retrieve all announced programs for this competition
        announced_progs = list(
            Program.objects.filter(competition=comp, is_announced=True).order_by('announced_at', 'id')
        )

        # If some programs have announced_at None, preserve their sequential order with fallback timestamps
        base_time = timezone.now()
        for idx, prog in enumerate(announced_progs, start=1):
            if not prog.announced_at:
                prog.announced_at = base_time
            prog.result_number = idx
            prog.save(update_fields=['result_number', 'announced_at'])

def reverse_func(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_programresultedithistory'),
    ]

    operations = [
        migrations.RunPython(reorder_announced_results, reverse_func),
    ]
