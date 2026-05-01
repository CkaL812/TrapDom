import os
from django.apps import AppConfig


class TrapappConfig(AppConfig):
    name = 'trapApp'

    def ready(self):
        import sys
        # Не запускаємо scheduler під час management команд (migrate, collectstatic тощо)
        if any(cmd in sys.argv for cmd in ('migrate', 'collectstatic', 'makemigrations', 'shell')):
            return
        run_main = os.environ.get('RUN_MAIN')
        if run_main == 'false':
            return
        self._start_scheduler()

    def _start_scheduler(self):
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.interval import IntervalTrigger
            from django_apscheduler.jobstores import DjangoJobStore
            from .tasks import check_and_send_reminders

            scheduler = BackgroundScheduler()
            scheduler.add_jobstore(DjangoJobStore(), 'default')
            scheduler.add_job(
                check_and_send_reminders,
                trigger=IntervalTrigger(minutes=15),
                id='check_and_send_reminders',
                max_instances=1,
                replace_existing=True,
            )
            scheduler.start()
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(f'[SCHEDULER] Не вдалось запустити: {exc}')
