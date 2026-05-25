import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trapApp', '0014_remove_admin_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='TryOnSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_id', models.CharField(db_index=True, max_length=36, unique=True)),
                ('status', models.CharField(
                    choices=[('processing', 'Обробляється'), ('done', 'Готово'), ('error', 'Помилка')],
                    default='processing',
                    max_length=20,
                )),
                ('result_image', models.CharField(blank=True, max_length=500)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tryon_sessions',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('items', models.ManyToManyField(
                    blank=True,
                    related_name='tryon_sessions',
                    to='trapApp.clothingitem',
                )),
            ],
            options={
                'verbose_name': 'Сесія примірки',
                'verbose_name_plural': 'Сесії примірки',
                'ordering': ['-created_at'],
            },
        ),
    ]
