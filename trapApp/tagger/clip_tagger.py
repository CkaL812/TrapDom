"""
ClipTagger — тагує товари CLIP-моделлю + правилами.

Використання:
    tagger = ClipTagger()            # завантажує модель (один раз)
    tagger.tag_items(queryset)       # тагує список товарів

Тагер робить для кожного товару:
  1. Скачує картинку за image_url
  2. Обчислює image embedding через CLIP (один раз на товар)
  3. Для 3 завдань (subcategory / style / formality) — text embeddings
     і знаходить найближчу відповідь через cosine similarity
  4. Проставляє time_of_day і age_ranges за ПРАВИЛАМИ (на основі
     визначених subcategory, style, formality)
  5. Зберігає tags, mark_tagged()
"""

import io
import logging
import time
from decimal import Decimal
from typing import List, Optional, Tuple

import requests
from django.db.models import QuerySet

from .tag_definitions import (
    SUBCATEGORY_PROMPTS,
    STYLE_PROMPTS,
    FORMALITY_PROMPTS,
    compute_time_of_day,
    compute_age_ranges,
)

log = logging.getLogger(__name__)


class ClipTagger:
    """
    Мінімальний поріг впевненості. Якщо CLIP впевнений менше — тег не ставиться,
    товар залишиться з tagged_at=NULL, щоб можна було переобробити пізніше.
    """
    MIN_CONFIDENCE = 0.22   # для CLIP це нормальне значення (не 0.5!)

    # Скільки top-N тегів брати для мультилейбл полів (styles)
    TOP_N_STYLES = 2

    # HTTP для завантаження фото
    IMAGE_TIMEOUT = 10
    IMAGE_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    def __init__(self, model_name='openai/clip-vit-base-patch32', device=None):
        """
        Завантажує модель при першому використанні.
        Ця ініціалізація важка (~1 хв + ~600 MB download при першому запуску).
        """
        log.info(f'[ClipTagger] Завантаження моделі {model_name}...')
        t0 = time.time()

        # Ліниві імпорти, щоб моделі не завантажувались при імпорті модуля
        import torch
        from transformers import CLIPModel, CLIPProcessor

        self.torch = torch
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')

        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.model.eval()
        self.processor = CLIPProcessor.from_pretrained(model_name)

        # Попередньо обчислюємо text embeddings для всіх промптів (один раз)
        log.info('[ClipTagger] Обчислення text embeddings...')
        self._style_emb = self._precompute_text_embeddings(STYLE_PROMPTS)
        self._formality_emb = self._precompute_text_embeddings(FORMALITY_PROMPTS)
        self._subcategory_emb = self._precompute_text_embeddings(SUBCATEGORY_PROMPTS)

        log.info(f'[ClipTagger] Готово за {time.time()-t0:.1f}s. Device: {self.device}')

    # ────────────────────────────────────────────────────────────
    #  PUBLIC API
    # ────────────────────────────────────────────────────────────
    def tag_items(self, queryset: QuerySet, skip_already_tagged=True) -> dict:
        """
        Тагує всі товари з queryset. Повертає статистику.

        skip_already_tagged=True → пропускає ті, що вже мають tagged_at
        """
        if skip_already_tagged:
            queryset = queryset.filter(tagged_at__isnull=True)

        total = queryset.count()
        if not total:
            log.info('[ClipTagger] Немає товарів для обробки')
            return {'total': 0, 'tagged': 0, 'skipped': 0, 'errors': 0}

        log.info(f'[ClipTagger] Обробка {total} товарів...')

        stats = {'total': total, 'tagged': 0, 'skipped': 0, 'errors': 0}
        t_start = time.time()

        for i, item in enumerate(queryset.iterator(), 1):
            try:
                ok = self._tag_single_item(item)
                if ok:
                    stats['tagged'] += 1
                else:
                    stats['skipped'] += 1
            except Exception as e:
                log.exception(f'[ClipTagger] помилка на #{item.pk} ({item.name}): {e}')
                stats['errors'] += 1

            # Прогрес кожні 10 товарів
            if i % 10 == 0 or i == total:
                elapsed = time.time() - t_start
                rate = i / elapsed if elapsed else 0
                eta = (total - i) / rate if rate else 0
                log.info(
                    f'[ClipTagger] {i}/{total} '
                    f'(tagged={stats["tagged"]}, skip={stats["skipped"]}, '
                    f'err={stats["errors"]}) '
                    f'• {rate:.1f} it/s • ETA ~{eta/60:.1f} min'
                )

        log.info(f'[ClipTagger] ✅ Завершено за {(time.time()-t_start)/60:.1f} min')
        log.info(f'[ClipTagger] {stats}')
        return stats

    # ────────────────────────────────────────────────────────────
    #  ОБРОБКА ОДНОГО ТОВАРУ
    # ────────────────────────────────────────────────────────────
    def _tag_single_item(self, item) -> bool:
        if not item.image_url:
            log.warning(f'  [{item.pk}] немає image_url — пропуск')
            return False

        # 1. Завантажуємо фото
        image = self._download_image(item.image_url)
        if image is None:
            return False

        # 2. Обчислюємо image embedding (ОДИН раз на товар)
        img_emb = self._compute_image_embedding(image)

        # 3. CLIP: subcategory (звужуємо до категорії товару)
        sub, sub_conf = self._classify_subcategory(img_emb, item.category)

        # 4. CLIP: formality
        formality, form_conf = self._classify(img_emb, self._formality_emb)

        # 5. CLIP: styles (top-N)
        styles_with_conf = self._classify_topn(img_emb, self._style_emb, n=self.TOP_N_STYLES)

        # 6. Застосовуємо тільки результати, які перевищують поріг
        updated_fields = []

        if sub and sub_conf >= self.MIN_CONFIDENCE:
            item.subcategory = sub
            updated_fields.append('subcategory')

        if formality and form_conf >= self.MIN_CONFIDENCE:
            item.formality = formality
            updated_fields.append('formality')

        # 7. ПРАВИЛА: time_of_day на основі subcategory
        item.set_time_of_day(compute_time_of_day(item.subcategory))

        # 8. ПРАВИЛА: age_ranges на основі styles + formality
        good_styles = [s for s, c in styles_with_conf if c >= self.MIN_CONFIDENCE]
        item.set_age_ranges(compute_age_ranges(good_styles, item.formality))

        # 9. Записуємо confidence у tags (для дебагу)
        item.set_confidence({
            'subcategory': round(float(sub_conf), 3),
            'formality':   round(float(form_conf), 3),
            'styles':      {s: round(float(c), 3) for s, c in styles_with_conf},
        })

        # 10. Зберігаємо: спочатку основні поля, потім M2M стилі
        updated_fields.append('tags')
        item.save(update_fields=updated_fields)

        if good_styles:
            item.set_styles(good_styles)

        item.mark_tagged(source='mixed')   # CLIP + правила
        return True

    # ────────────────────────────────────────────────────────────
    #  ЗАВАНТАЖЕННЯ ФОТО
    # ────────────────────────────────────────────────────────────
    def _download_image(self, url: str):
        from PIL import Image
        try:
            r = requests.get(url, headers=self.IMAGE_HEADERS, timeout=self.IMAGE_TIMEOUT)
            if r.status_code != 200:
                log.warning(f'  [IMG] статус {r.status_code} для {url[:80]}')
                return None
            img = Image.open(io.BytesIO(r.content)).convert('RGB')
            return img
        except Exception as e:
            log.warning(f'  [IMG] не вдалось завантажити: {e}')
            return None

    # ────────────────────────────────────────────────────────────
    #  ОБЧИСЛЕННЯ EMBEDDINGS
    # ────────────────────────────────────────────────────────────
    def _compute_image_embedding(self, image):
        torch = self.torch
        inputs = self.processor(images=image, return_tensors='pt').to(self.device)
        with torch.no_grad():
            vision_out = self.model.vision_model(**inputs)
            emb = self.model.visual_projection(vision_out.pooler_output)
        emb = emb / emb.norm(dim=-1, keepdim=True)
        return emb  # shape [1, 512]

    def _precompute_text_embeddings(self, prompts_dict: dict) -> Tuple[list, 'torch.Tensor']:
        """
        Повертає (labels, tensor_embeddings)
          labels: список ключів у порядку embeddings
          embeddings: tensor shape [len(labels), 512]
        """
        torch = self.torch
        labels = list(prompts_dict.keys())
        texts = [prompts_dict[k] for k in labels]

        inputs = self.processor(text=texts, return_tensors='pt', padding=True).to(self.device)
        with torch.no_grad():
            text_out = self.model.text_model(**inputs)
            emb = self.model.text_projection(text_out.pooler_output)
        emb = emb / emb.norm(dim=-1, keepdim=True)
        return labels, emb

    # ────────────────────────────────────────────────────────────
    #  КЛАСИФІКАЦІЯ
    # ────────────────────────────────────────────────────────────
    def _similarity(self, img_emb, text_emb):
        """Повертає tensor [N] cosine similarity."""
        return (img_emb @ text_emb.T).squeeze(0)

    def _classify(self, img_emb, label_emb_pair) -> Tuple[Optional[str], float]:
        """Повертає найкращий label + його score."""
        labels, text_emb = label_emb_pair
        sims = self._similarity(img_emb, text_emb)
        probs = sims.softmax(dim=-1)
        top_idx = int(probs.argmax())
        return labels[top_idx], float(probs[top_idx])

    def _classify_topn(self, img_emb, label_emb_pair, n=2) -> List[Tuple[str, float]]:
        """Повертає top-N (label, score)."""
        labels, text_emb = label_emb_pair
        sims = self._similarity(img_emb, text_emb)
        probs = sims.softmax(dim=-1)
        top = self.torch.topk(probs, k=min(n, len(labels)))
        return [(labels[int(i)], float(v)) for v, i in zip(top.values, top.indices)]

    def _classify_subcategory(self, img_emb, category: str) -> Tuple[Optional[str], float]:
        """
        Спеціальна класифікація підкатегорії: беремо лише підкатегорії,
        що відповідають основній category товару.
        """
        from trapApp.models import ClothingItem

        allowed_subcats = ClothingItem.SUBCATEGORY_BY_CATEGORY.get(category, [])
        if not allowed_subcats:
            # Якщо category невідома — беремо всі
            return self._classify(img_emb, self._subcategory_emb)

        # Фільтруємо precomputed embeddings
        all_labels, all_emb = self._subcategory_emb
        indices = [all_labels.index(s) for s in allowed_subcats if s in all_labels]
        if not indices:
            return None, 0.0

        filtered_emb = all_emb[indices]
        filtered_labels = [all_labels[i] for i in indices]

        sims = self._similarity(img_emb, filtered_emb)
        probs = sims.softmax(dim=-1)
        top_idx = int(probs.argmax())
        return filtered_labels[top_idx], float(probs[top_idx])