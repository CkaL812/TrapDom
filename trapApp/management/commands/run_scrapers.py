from django.core.management.base import BaseCommand
from trapApp.scrapers.zara import ZaraScraper
from trapApp.scrapers.cos import CosScraper
from trapApp.scrapers.hugo_boss import HugoBossScraper
from trapApp.scrapers.massimo_dutti import MassimoDuttiScraper
from trapApp.scrapers.ralph_lauren import RalphLaurenScraper
from trapApp.scrapers.levis import LevisScraper
from trapApp.scrapers.diesel import DieselScraper
from trapApp.scrapers.guess import GuessScraper
from trapApp.scrapers.suitsupply import SuitsupplyScraper
from trapApp.scrapers.ted_baker import TedBakerScraper
from trapApp.scrapers.ed_hardy import EdHardyScraper
from trapApp.scrapers.farfetch import TomFordScraper, GiorgioArmaniScraper, SandroScraper

SCRAPERS = [
    ZaraScraper,
    CosScraper,
    MassimoDuttiScraper,
    RalphLaurenScraper,
    HugoBossScraper,
    LevisScraper,
    DieselScraper,
    GuessScraper,
    SuitsupplyScraper,
    TedBakerScraper,
    EdHardyScraper,
    TomFordScraper,
    GiorgioArmaniScraper,
    SandroScraper,
]

BRAND_ALIASES = {
    'zara':    ZaraScraper,
    'cos':     CosScraper,
    'massimo': MassimoDuttiScraper,
    'ralph':   RalphLaurenScraper,
    'hugo':    HugoBossScraper,
    'levis':   LevisScraper,
    'diesel':  DieselScraper,
    'guess':   GuessScraper,
    'suits':   SuitsupplyScraper,
    'ted':     TedBakerScraper,
    'ed':      EdHardyScraper,
    'tomford': TomFordScraper,
    'armani':  GiorgioArmaniScraper,
    'sandro':  SandroScraper,
}


class Command(BaseCommand):
    help = 'Run all (or selected) brand scrapers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--brand',
            type=str,
            default='all',
            help=f'Бренд: {", ".join(BRAND_ALIASES.keys())}, all'
        )

    def handle(self, *args, **options):
        brand = options['brand'].lower().replace('-', '').replace(' ', '')
        to_run = SCRAPERS if brand == 'all' else [BRAND_ALIASES.get(brand)]

        if not to_run or None in to_run:
            self.stdout.write(self.style.ERROR(f'Невідомий бренд: {options["brand"]}'))
            return

        ok, fail = 0, 0
        for ScraperClass in to_run:
            s = ScraperClass()
            self.stdout.write(f'[→] {s.brand_name}')
            try:
                s.run()
                self.stdout.write(self.style.SUCCESS(f'[✓] {s.brand_name}'))
                ok += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'[✗] {s.brand_name}: {e}'))
                fail += 1

        self.stdout.write('─' * 40)
        self.stdout.write(
            self.style.SUCCESS(f'Успішно: {ok}') + f' | Помилок: {fail}'
        )