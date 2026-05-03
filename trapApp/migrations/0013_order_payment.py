from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trapApp', '0012_order_orderitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_status',
            field=models.CharField(default='unpaid', max_length=20),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_intent_id',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
