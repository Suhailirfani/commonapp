from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_separate_single_group_points'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='start_chest_no',
            field=models.PositiveIntegerField(default=1001, help_text='Starting chest number sequence for contestants in this category'),
        ),
    ]
