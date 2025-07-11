# Generated by Django 5.2.3 on 2025-06-30 13:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ValdivianoApp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Boleta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('total', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='DetalleBoleta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('precio', models.DecimalField(decimal_places=2, max_digits=10)),
                ('cantidad', models.DecimalField(decimal_places=3, max_digits=10)),
                ('total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('boleta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='ValdivianoApp.boleta')),
            ],
        ),
    ]
