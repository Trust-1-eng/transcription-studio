# AssemblyAI Transcription Studio — Manifest & Roadmap
> Версия 2 — исправления + предложения по улучшению

---

## Проект

**Название**: AssemblyAI Transcription Studio
**Модель**: Universal-2 (99 языков, включая UA/RU)
**Тип**: Локальный веб-сервис (запускается на своём компьютере)
**Цель**: Полный контроль над транскрипцией через AssemblyAI API —
загрузка видео/аудио/URL, все настройки через toggle-слайдеры, экспорт в любой формат

---

## Стек

| Слой | Технология | Зачем |
|---|---|---|
| Backend | Python 3.11+ + FastAPI | REST API, обработка файлов, конвертация экспортов |
| Frontend | Vanilla HTML/CSS/JS | Нет сборки, открывается напрямую в браузере |
| Аудио из видео | FFmpeg (системная утилита) | Извлечь аудио из .mp4 .mkv .avi .mov и др. |
| Загрузка по URL | yt-dlp | YouTube, Vimeo, SoundCloud, 1000+ сайтов, лучшее качество |
| AssemblyAI | REST API напрямую (без SDK) | Полный контроль всех параметров + speech_understanding |
| Word (.docx) | python-docx | Форматированный Word-документ |
| PDF | fpdf2 + DejaVuSans.ttf | PDF с полной поддержкой кириллицы |
| ZIP архив | zipfile (stdlib) | Скачать все форматы одним файлом |
| Окружение | python-dotenv | API ключ из .env |

---

## UI-принципы

- **Все настройки** — toggle-слайдеры (вкл/выкл), не чекбоксы
- **Числовые значения** — ползунки (range sliders)
- **Языки** — searchable dropdown (поиск по названию и коду)
- **Язык транскрипции** — кнопка-переключатель `[АВТО] / [ВИБРАТИ]`
  - АВТО = `language_detection: true`
  - ВИБРАТИ = searchable dropdown 99 языков Universal-2
- **Выключенные опции** — отображаются серыми, не скрываются

---

## Архитектура — поток данных

```
ИСТОЧНИК
├── Файл (видео/аудио) → drag & drop или browse
│   ├── Видео (.mp4 .mkv .avi .mov .wmv …) → FFmpeg → .mp3
│   └── Аудио (.mp3 .wav .flac .m4a .ogg …) → без изменений
└── URL → поле ввода
    └── yt-dlp --extract-audio --audio-quality 0 → .mp3
          │
          ▼
    POST /v2/upload  → upload_url  (CDN AssemblyAI)
          │
          ▼
    POST /v2/transcript  ← все параметры конфигурации
    + speech_understanding { translation, speaker_identification, custom_formatting }
          │
          ▼
    SSE /api/status/{id}  ← сервер тянет статус из AssemblyAI и
    или polling каждые 3с    пушит обновления в браузер
          │
          ▼
    Статус: queued → processing → completed / error
          │
          ▼
    РЕЗУЛЬТАТЫ → параллельный рендер в UI
    + конвертация в форматы → скачивание / ZIP
```

---

## Функции и API-маппинг

### Источник / Подготовка аудио

| Функция | Инструмент | Детали |
|---|---|---|
| Файл видео | FFmpeg | `-vn -acodec libmp3lame -ab 192k -ar 44100` |
| Файл аудио | напрямую | поддерживаемые форматы без перекодировки |
| URL (YouTube и др.) | yt-dlp | `--extract-audio --audio-format mp3 --audio-quality 0 --no-playlist` |
| Загрузка на CDN | `POST /v2/upload` | стриминг по байтам |

---

### Язык транскрипции

| Функция UI | API параметр | UA/RU |
|---|---|---|
| Авто (кнопка АВТО) | `language_detection: true` | ✅ |
| Ручной выбор (кнопка ВИБРАТИ) | `language_code: "uk"` | ✅ |
| Code Switching toggle | `language_detection_options.code_switching: true` | ✅ |
| Языки code switching | `language_detection_options.expected_languages: [...]` | ✅ |
| Confidence threshold | `language_confidence_threshold: 0.7` | ✅ |

**Universal-2 — 99 языков для распознавания:**
af · am · ar · as · az · ba · be · bg · bn · bo · br · bs · ca · cs · cy · da · de · el
en · en_au · en_uk · en_us · es · et · eu · fa · fi · fo · fr · gl · gu · ha · haw · he
hi · hr · ht · hu · hy · id · is · it · ja · jw · ka · kk · km · kn · ko · la · lb · ln
lo · lt · lv · mg · mi · mk · ml · mn · mr · ms · mt · my · ne · nl · nn · no · oc · pa
pl · ps · pt · ro · ru · sa · sd · si · sk · sl · sn · so · sq · sr · su · sv · sw · ta
te · tg · th · tk · tl · tr · tt · **uk** · ur · uz · vi · yi · yo · zh

---

### Speaker (Диаризация)

| Функция UI | API параметр | UA/RU |
|---|---|---|
| Speaker Labels toggle | `speaker_labels: true` | ✅ |
| Кол-во спикеров (ползунок 1–10) | `speakers_expected: N` | ✅ |
| Speaker ID toggle | `speech_understanding.request.speaker_identification` | ✅ |
| Тип: Имя | `speaker_type: "name"`, `known_values: [...]` | ✅ |
| Тип: Роль | `speaker_type: "role"`, `known_values: [...]` | ✅ |
| Описание спикера | `speakers: [{value: "...", description: "..."}]` | ✅ |
| Multichannel toggle | `multichannel: true` | ✅ |

---

### Форматирование текста

| Функция UI | API параметр | UA/RU |
|---|---|---|
| Auto Punctuation toggle | `punctuate: true` | ✅ |
| Text Formatting toggle | `format_text: true` | ✅ |
| Filler Words toggle | `disfluencies: true` | ✅ |
| Filter Profanity toggle | `filter_profanity: true` | ❌ только EN |
| Custom Formatting — Дата | `speech_understanding.request.custom_formatting.date` | ✅ |
| Custom Formatting — Телефон | `speech_understanding.request.custom_formatting.phone_number` | ✅ |
| Custom Formatting — Email | `speech_understanding.request.custom_formatting.email` | ✅ |
| Remove Audio Tags toggle | `remove_audio_tags: "all"` | ✅ убирает [MUSIC] [NOISE] |

---

### Перевод (80+ языков)

| Функция UI | API параметр | UA/RU |
|---|---|---|
| Перевести на → (searchable) | `speech_understanding.request.translation.target_languages: [...]` | ✅ |
| Несколько языков сразу | массив из 2–3 кодов | ✅ |
| Формальный стиль toggle | `speech_understanding.request.translation.formal: true` | ✅ |
| Перевод по репликам toggle | `speech_understanding.request.translation.match_original_utterance: true` | ✅ |

**80+ языков перевода** (с поиском в UI):
af · am · ar · as · az · be · bg · bn · bo · br · bs · ca · cs · cy · da · de · el
**en** · en_au · en_uk · en_us · es · et · eu · fa · fi · fo · fr · gl · gu · ha · haw
he · hi · hr · ht · hu · hy · id · is · it · ja · jw · ka · kk · km · kn · ko · la · lb
ln · lo · lt · lv · mg · mi · mk · ml · mn · mr · ms · mt · my · ne · nl · no · pa · pl
ps · pt · ro · **ru** · sd · si · sk · sl · sn · so · sq · sr · su · sv · sw · ta · te · tg
th · tk · tl · tr · **uk** · ur · uz · vi · yi · yo · zh

---

### PII Redaction

| Функция UI | API параметр | UA/RU |
|---|---|---|
| PII toggle | `redact_pii: true` | ✅ 99%+ для RU/UK |
| Выбор типов (toggles-сетка) | `redact_pii_policies: [...]` | ✅ |
| Метод замены | `redact_pii_sub: "entity_name"/"hash"` | ✅ |
| Redact Audio toggle | `redact_pii_audio: true` | ✅ |
| Формат аудио | `redact_pii_audio_quality: "mp3"/"wav"` | ✅ |
| Метод аудио | `override_audio_redaction_method: "beep"/"silence"` | ✅ |

**50+ типов PII:**
`person_name` · `phone_number` · `email_address` · `location` · `date_of_birth`
`credit_card_number` · `credit_card_cvv` · `credit_card_expiration`
`banking_information` · `us_social_security_number` · `passport_number`
`drivers_license` · `healthcare_number` · `medical_condition` · `medical_process`
`drug` · `injury` · `organization` · `occupation` · `ip_address` · `url`
`username` · `password` · `money_amount` · `date` · `date_interval` · `time`
`duration` · `event` · `vehicle_id` · `blood_type` · `gender_sexuality`
`marital_status` · `nationality` · `religion` · `political_affiliation`
`physical_attribute` · `zodiac_sign` · `number_sequence` · `statistics`
`filename` · `language` · `person_age`

---

### Medical Mode

| Функция UI | API параметр | UA/RU | EN/ES/DE/FR |
|---|---|---|---|
| Medical Mode toggle | `domain: "medical-v1"` | ✅ доступно | ✅ полная поддержка |

> Примечание: UI AssemblyAI показывает Medical mode доступным для всех языков.
> Для EN/ES/DE/FR — полная оптимизация под медтерминологию.
> Для UA/RU — модель принимает параметр, результат улучшения зависит от контекста.

---

### Speech Understanding — только EN (English Pro)

| Функция UI | API параметр | UA/RU |
|---|---|---|
| Entity Detection toggle | `entity_detection: true` | ✅ частично |
| Sentiment Analysis toggle | `sentiment_analysis: true` | ❌ только EN |
| Content Safety toggle | `content_safety: true` | ❌ только EN |
| Content Safety confidence (ползунок) | `content_safety_confidence: 25–100` | ❌ |
| IAB Topic Detection toggle | `iab_categories: true` | ❌ только EN |
| Auto Highlights toggle | `auto_highlights: true` | ❌ только EN |

---

### Точность / Дополнительно

| Функция UI | API параметр | UA/RU |
|---|---|---|
| Key Terms (теги) | `keyterms_prompt: [...]` до 200 | ✅ |
| Custom Spelling (пары замены) | `custom_spelling: [{from:[...], to:"..."}]` | ✅ |
| Speech Threshold (ползунок) | `speech_threshold: 0.0–1.0` | ✅ |
| Audio Trim From (ввод мс) | `audio_start_from: мс` | ✅ |
| Audio Trim To (ввод мс) | `audio_end_at: мс` | ✅ |

---

## Экспорт — полная матрица форматов

### Транскрипция (поле `text` / `utterances`)

| # | Файл | Содержит | Источник данных |
|---|---|---|---|
| 1 | `transcript.txt` | Чистый текст | `transcript.text` |
| 2 | `transcript.docx` | Word со спикерами и временем | python-docx |
| 3 | `transcript.pdf` | PDF с кириллицей | fpdf2 + DejaVuSans |
| 4 | `transcript.md` | Markdown с секциями по спикерам | конвертация |

### Абзацы — `/v2/transcript/{id}/paragraphs`

> AssemblyAI делит текст на логические абзацы по паузам и смыслу

| # | Файл | Содержит | Источник |
|---|---|---|---|
| 5 | `paragraphs.txt` | Текст с пустыми строками между абзацами | конвертация JSON |
| 6 | `paragraphs.docx` | Word — каждый абзац = параграф | python-docx |
| 7 | `paragraphs.pdf` | PDF с разбивкой | fpdf2 |
| 8 | `paragraphs.md` | Markdown | конвертация |
| 9 | `paragraphs.json` | Оригинал с координатами и словами | API напрямую |

### Предложения — `/v2/transcript/{id}/sentences`

> Каждое предложение отдельно с временными метками — удобно для анализа

| # | Файл | Содержит | Источник |
|---|---|---|---|
| 10 | `sentences_timestamped.txt` | `[00:01:23] Текст предложения.` | конвертация |
| 11 | `sentences.csv` | `start_ms, end_ms, time, text, confidence` | конвертация |
| 12 | `sentences.srt` | Subtitle-файл, 1 предложение = 1 субтитр | конвертация |
| 13 | `sentences.json` | Сырой JSON | API напрямую |

### Субтитры — прямо из API

| # | Файл | Содержит | Источник |
|---|---|---|---|
| 14 | `captions.srt` | Стандартные субтитры | `GET /v2/transcript/{id}/srt` |
| 15 | `captions.vtt` | WebVTT для HTML5 плееров | `GET /v2/transcript/{id}/vtt` |

### Слова с таймстемпами — из `transcript.words`

| # | Файл | Содержит | Источник |
|---|---|---|---|
| 16 | `words.csv` | `start_ms, end_ms, word, confidence` | конвертация |
| 17 | `words.json` | Каждое слово с временными метками | из ответа API |

### Таблица — форматированная таблица со спикерами

| # | Файл | Содержит | Источник данных |
|---|---|---|---|
| 18 | `table.docx` | Word-таблица: № / Таймкод / Спікер / Текст | python-docx |
| 19 | `table.pdf` | PDF-таблица с тёмным заголовком и чередованием строк | fpdf2 |

### Літературна/сценарна — чистий діалог без таймкодів

| # | Файл | Содержит | Источник данных |
|---|---|---|---|
| 20 | `literary.txt` | `— Спікер: Текст` (em-dash діалог) | конвертация |
| 21 | `literary.docx` | Word: збільшений інтервал, широкі поля, bold спікери | python-docx |

### Інтерв'ю — формат Q&A

| # | Файл | Содержит | Источник данных |
|---|---|---|---|
| 22 | `interview.docx` | Запитання жирним, відповіді з відступом 1см | python-docx |

> Автоматично визначає інтерв'юера (перший спікер у транскрипті)

### Дослівна з анотаціями — verbatim transcript

| # | Файл | Содержит | Источник данных |
|---|---|---|---|
| 23 | `verbatim.txt` | Текст + `(пауза — X сек)`, `(довга пауза)`, `(перебив)` | аналіз таймстемпів |
| 24 | `verbatim.docx` | Word: анотації центровані, помаранчеві, курсив | python-docx |

> Паузи визначаються автоматично: 3-8с = пауза, 8+с = довга пауза, перекриття >200мс = перебив

### Перевод — из `speech_understanding.results.translation`

| # | Файл | Содержит | Источник |
|---|---|---|---|
| 25 | `translation_{lang}.txt` | Чистый текст перевода | конвертация |
| 26 | `translation_{lang}.docx` | Word файл | python-docx |
| 27 | `translation_{lang}.srt` | Субтитры на целевом языке | по utterances |
| 28 | `translation_{lang}.vtt` | VTT субтитры | конвертация |

### Двомовна — оригінал + переклад

| # | Файл | Содержит | Источник данных |
|---|---|---|---|
| 29 | `bilingual_{lang}.txt` | Оригінал + `→ переклад` рядок за рядком | конвертация |
| 30 | `bilingual_{lang}.docx` | Word: оригінал bold, переклад курсив сірим | python-docx |

> Якщо обрано 2–3 мови перекладу — кожна мова окремою групою

### Аналитика (только EN)

| # | Файл | Содержит | Источник |
|---|---|---|---|
| 31 | `entities.csv` | `entity_type, text, start_ms, end_ms` | конвертация |
| 32 | `sentiment.csv` | `sentence, sentiment, confidence` | конвертация |
| 33 | `topics_iab.json` | IAB категории с confidence | из API |
| 34 | `highlights.txt` | Ключевые фразы | конвертация |

### Redacted Audio

| # | Файл | Содержит | Источник |
|---|---|---|---|
| 35 | `redacted.mp3` / `.wav` | Аудио с тихими/запиканными PII | `redacted_audio_url` |

### ZIP-бандл

| # | Файл | Содержит |
|---|---|---|
| 36 | `transcript_bundle.zip` | Все выбранные форматы одним кликом |

---

## Языковая матрица — итог

| Функция | UA ✅/❌ | RU ✅/❌ | Только EN |
|---|---|---|---|
| Транскрипция Universal-2 | ✅ | ✅ | — |
| Speaker Labels | ✅ | ✅ | — |
| Speaker ID (имена/роли) | ✅ | ✅ | — |
| Language Detection | ✅ | ✅ | — |
| Code Switching | ✅ | ✅ | — |
| Auto Punctuation | ✅ | ✅ | — |
| Text Formatting | ✅ | ✅ | — |
| Filler Words | ✅ | ✅ | — |
| Custom Formatting | ✅ | ✅ | — |
| Key Terms | ✅ | ✅ | — |
| Custom Spelling | ✅ | ✅ | — |
| PII Redaction | ✅ | ✅ | — |
| Redacted Audio | ✅ | ✅ | — |
| Entity Detection | ✅ частично | ✅ частично | — |
| Translation | ✅ источник | ✅ источник | — |
| Medical Mode | ✅ доступно | ✅ доступно | полная оптимизация |
| Remove Audio Tags | ✅ | ✅ | — |
| Filter Profanity | ❌ | ❌ | ✅ |
| Sentiment Analysis | ❌ | ❌ | ✅ |
| Content Safety | ❌ | ❌ | ✅ |
| IAB Categories | ❌ | ❌ | ✅ |
| Auto Highlights | ❌ | ❌ | ✅ |

---

## Предложения по улучшению

### UX / Frontend

| # | Идея | Ценность | Сложность |
|---|---|---|---|
| 1 | **Аудиоплеер** — после транскрипции плеер прямо в UI, клик на слово = прыжок во времени | ⭐⭐⭐ высокая | средняя |
| 2 | **Inline редактор** — исправить ошибки в тексте до экспорта | ⭐⭐⭐ высокая | средняя |
| 3 | **Confidence-подсветка** — слова с низким confidence выделяются жёлтым/красным | ⭐⭐ средняя | низкая |
| 4 | **Dual-view перевод** — оригинал и перевод рядом колонками | ⭐⭐ средняя | низкая |
| 5 | **История сессий** — 10 последних транскриптов в localStorage (ID + название + дата) | ⭐⭐⭐ высокая | низкая |
| 6 | **Presets настроек** — сохранить конфигурацию ("Медицина UA", "Интервью EN") | ⭐⭐ средняя | низкая |
| 7 | **Прогресс-статус** — показывать реальные сообщения "queued → processing → completed" | ⭐⭐ средняя | низкая |

### Архитектура / Backend

| # | Идея | Ценность | Сложность |
|---|---|---|---|
| 8 | **SSE (Server-Sent Events)** вместо polling — сервер сам пушит статус, нет лишних запросов | ⭐⭐ средняя | средняя |
| 9 | **Resumable transcription** — ввести существующий ID транскрипта и загрузить результаты (AssemblyAI хранит 90 дней) | ⭐⭐⭐ высокая | низкая |
| 10 | **Health check** — `GET /health` проверяет валидность API ключа при старте | ⭐⭐ | низкая |
| 11 | **Авто-очистка temp** — background task удаляет файлы старше 2 часов | ⭐⭐ | низкая |
| 12 | **Стриминг больших файлов** — upload через chunks, не загружать весь файл в память | ⭐⭐ | средняя |

### Фичи

| # | Идея | Ценность | Сложность |
|---|---|---|---|
| 13 | **Несколько языков перевода одновременно** — выбрать 2–3 языка, один запрос | ⭐⭐⭐ высокая | низкая |
| 14 | **Remove Audio Tags** — убирает `[MUSIC]` `[NOISE]` `[APPLAUSE]` из текста | ⭐⭐ | низкая |
| 15 | **Batch upload** — несколько файлов в очереди | ⭐⭐ | высокая |
| 16 | **Download All ZIP** — все выбранные форматы одним кликом | ⭐⭐⭐ высокая | низкая |
| 17 | **Субтитры перевода** — если включён match_original_utterance, генерировать SRT/VTT на переведённом языке | ⭐⭐⭐ | средняя |
| 18 | **Авто-имя файла** — из заголовка видео (yt-dlp возвращает title) или имени файла | ⭐⭐ | низкая |

### Что берём в Фазу 1

- Пункты 1 (плеер), 5 (история), 9 (resumable ID), 10 (health), 11 (cleanup), 13 (мульти-перевод), 14 (audio tags), 16 (ZIP), 18 (авто-имя)

---

## Дорожная карта

### Фаза 1 — Ядро (строим сейчас)
- [ ] FFmpeg экстракция + yt-dlp загрузка
- [ ] Upload на CDN AssemblyAI
- [ ] Базовая транскрипция (язык авто/ручной, punctuate, format_text, disfluencies)
- [ ] Polling/SSE статуса с прогресс-сообщениями
- [ ] Экспорт: TXT, DOCX, PDF, MD, SRT, VTT, CSV, JSON, ZIP
- [ ] History (localStorage) + Resumable ID
- [ ] Health check эндпоинт
- [ ] Авто-очистка temp файлов

### Фаза 2 — Speaker Features
- [ ] Speaker Labels + Expected count
- [ ] Speaker Identification (имена/роли + описание)
- [ ] Multichannel
- [ ] Confidence-подсветка в UI

### Фаза 3 — Форматирование и язык
- [ ] Custom Formatting (дата, телефон, email)
- [ ] Code Switching
- [ ] Key Terms (теги в UI)
- [ ] Custom Spelling (пары замены)
- [ ] Remove Audio Tags
- [ ] Filter Profanity (EN only — с пометкой)

### Фаза 4 — Экспорт Pro
- [ ] Paragraphs → TXT/DOCX/PDF/MD/JSON
- [ ] Sentences → TXT/CSV/SRT/JSON
- [ ] Words → CSV/JSON
- [ ] Translation multi-lang → TXT/DOCX/SRT/VTT
- [ ] ZIP-бандл "Download All"
- [ ] Inline редактор транскрипции
- [ ] Аудиоплеер с синхронизацией

### Фаза 5 — Intelligence & PII
- [ ] PII Redaction (50+ типов, полная сетка toggles)
- [ ] Redacted Audio скачивание
- [ ] Medical Mode
- [ ] Entity Detection

### Фаза 6 — English Pro
- [ ] Sentiment Analysis
- [ ] Content Safety + ползунок confidence
- [ ] IAB Categories
- [ ] Auto Highlights
- [ ] Dual-view перевод
- [ ] Settings Presets

---

## Зависимости

```bash
# Python пакеты
pip install fastapi uvicorn python-multipart python-dotenv \
            requests python-docx fpdf2

# Системные утилиты
brew install ffmpeg        # macOS
pip install yt-dlp
```

## Структура файлов

```
Assembly Transcription/
├── MANIFEST.md             ← этот файл
├── CLAUDE.md               ← инструкции для Claude Code
├── SKILL.md                ← AssemblyAI API reference
├── main.py                 ← FastAPI app creation, lifespan, router mounting
├── requirements.txt
├── .env                    ← ASSEMBLYAI_API_KEY=... GEMINI_API_KEY=... (не коммитить)
├── .env.example            ← ASSEMBLYAI_API_KEY=your_key_here
├── app/
│   ├── config.py           ← API keys, paths, constants
│   ├── dependencies.py     ← shared state: caches, locks
│   ├── assemblyai_client.py ← REST API calls to AssemblyAI
│   ├── gemini_service.py   ← Gemini API integration
│   ├── utils.py            ← font download, ffmpeg/yt-dlp, time formatting
│   ├── routes/
│   │   ├── core.py         ← index, health, upload, transcribe, poll, gemini
│   │   └── export.py       ← ~30 export endpoints + ZIP bundle
│   └── exporters/
│       ├── helpers.py      ← resolve_speakers, make_doc_header, dl_headers
│       ├── text.py         ← TXT: standard, verbatim, bilingual, literary
│       ├── document.py     ← DOCX: standard, verbatim, bilingual, literary, interview
│       ├── pdf.py          ← PDF with Cyrillic (fpdf2 + DejaVuSans)
│       ├── table.py        ← table DOCX + PDF
│       └── subtitles.py    ← SRT/VTT for translations
├── fonts/
│   └── DejaVuSans.ttf     ← скачивается автоматически при первом запуске
├── temp/                   ← аудио-файлы (очищаются через 2 часа)
├── tests/
│   ├── test_ui.py          ← Playwright UI tests (58 checks)
│   └── test_api.sh         ← API endpoint tests
├── docs/                   ← language function libraries
└── static/
    ├── index.html          ← весь UI (steps: Source → Options → Results)
    ├── style.css           ← dark theme, toggles, sliders
    ├── app.js              ← вся логика (upload, poll, export, history)
    └── data.js             ← language lists, PII policy arrays
```
