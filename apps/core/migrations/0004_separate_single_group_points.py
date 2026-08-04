from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_category_included_categories_category_is_common'),
    ]

    operations = [
        migrations.RemoveField(model_name='pointsconfig', name='rank_1_points'),
        migrations.RemoveField(model_name='pointsconfig', name='rank_2_points'),
        migrations.RemoveField(model_name='pointsconfig', name='rank_3_points'),
        migrations.RemoveField(model_name='pointsconfig', name='grade_a_points'),
        migrations.RemoveField(model_name='pointsconfig', name='grade_b_points'),
        migrations.RemoveField(model_name='pointsconfig', name='grade_c_points'),

        migrations.AddField(model_name='pointsconfig', name='single_rank_1_points', field=models.IntegerField(default=5)),
        migrations.AddField(model_name='pointsconfig', name='single_rank_2_points', field=models.IntegerField(default=3)),
        migrations.AddField(model_name='pointsconfig', name='single_rank_3_points', field=models.IntegerField(default=1)),
        migrations.AddField(model_name='pointsconfig', name='single_grade_aplus_points', field=models.IntegerField(default=6)),
        migrations.AddField(model_name='pointsconfig', name='single_grade_a_points', field=models.IntegerField(default=5)),
        migrations.AddField(model_name='pointsconfig', name='single_grade_b_points', field=models.IntegerField(default=3)),
        migrations.AddField(model_name='pointsconfig', name='single_grade_c_points', field=models.IntegerField(default=1)),

        migrations.AddField(model_name='pointsconfig', name='group_rank_1_points', field=models.IntegerField(default=10)),
        migrations.AddField(model_name='pointsconfig', name='group_rank_2_points', field=models.IntegerField(default=6)),
        migrations.AddField(model_name='pointsconfig', name='group_rank_3_points', field=models.IntegerField(default=3)),
        migrations.AddField(model_name='pointsconfig', name='group_grade_aplus_points', field=models.IntegerField(default=6)),
        migrations.AddField(model_name='pointsconfig', name='group_grade_a_points', field=models.IntegerField(default=5)),
        migrations.AddField(model_name='pointsconfig', name='group_grade_b_points', field=models.IntegerField(default=3)),
        migrations.AddField(model_name='pointsconfig', name='group_grade_c_points', field=models.IntegerField(default=1)),

        migrations.AddField(model_name='pointsconfig', name='grade_aplus_threshold', field=models.IntegerField(default=90)),
    ]
