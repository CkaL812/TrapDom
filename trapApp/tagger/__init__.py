"""
Tagger package: автоматичне проставлення тегів (subcategory, style, formality,
time_of_day, age_ranges) через CLIP + правила.

Імпорт тагера ледачий — завантаження torch/transformers відбувається
тільки коли хтось реально викликає get_tagger().
"""

_tagger_instance = None


def get_tagger():
    """
    Повертає сингл-інстанс ClipTagger. Модель завантажується при першому виклику.
    """
    global _tagger_instance
    if _tagger_instance is None:
        from .clip_tagger import ClipTagger
        _tagger_instance = ClipTagger()
    return _tagger_instance


def reset_tagger():
    """Скинути інстанс (напр. для тестів або звільнення пам'яті)."""
    global _tagger_instance
    _tagger_instance = None