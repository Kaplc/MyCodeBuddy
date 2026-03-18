# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0004_add_last_result'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflow',
            name='bubble_records',
            field=models.TextField(blank=True, default='[]', verbose_name='气泡流记录'),
        ),
    ]
