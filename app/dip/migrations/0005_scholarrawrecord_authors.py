# Generated by Django 5.2 on 2025-05-31 21:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dip', '0004_remove_scholarrawrecord_authors'),
    ]

    operations = [
        migrations.AddField(
            model_name='scholarrawrecord',
            name='authors',
            field=models.ManyToManyField(blank=True, related_name='scholar_raw_records', to='dip.scholarauthor'),
        ),
    ]
