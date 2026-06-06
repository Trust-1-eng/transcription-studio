# 📚 ПОЛНЫЙ СПРАВОЧНИК ФУНКЦИЙ AssemblyAI для РУ и УА

**Дата:** April 2026
**Язык:** Русский/Украинский (Universal-2)

---

## 🎯 БАЗОВЫЕ ФУНКЦИИ (Ядро - Всегда работают)

### 1. **Speech-to-Text** (основа всего)

**Название в AssemblyAI:** Speech-to-Text / Transcription

**Что делает:**
- Преобразует аудио/видео в текст
- Распознает речь на русском/украинском
- Создает полный текст из видеофайла

**Как включить:** Автоматически при загрузке аудио

**Доступные форматы для скачивания:**
```
✅ Transcript text (.txt)
✅ Paragraphs (.json)
✅ Sentences (.json)
✅ Word-level timestamps (.json)
✅ Full JSON response
```

**Результат на практике:**
```
Аудио: "Вот что происходит с речью... когда... короче..."
↓
Результат: полный текст в TXT или JSON
```

---

### 2. **Auto Punctuation** (автоматическая пунктуация)

**Название в AssemblyAI:** Auto Punctuation

**Что делает:**
- Автоматически добавляет точки, запятые, вопросительные знаки
- Делает текст читаемым (без этого просто слова подряд)
- Расставляет знаки препинания по смыслу

**Как включить:** Playground → Settings → Auto Punctuation: ON

**Доступные форматы для скачивания:**
```
✅ Transcript text (.txt) - с пунктуацией
✅ Paragraphs (.json) - с пунктуацией
✅ Sentences (.json) - с пунктуацией
```

**Результат на практике:**
```
ДО:  вот что происходит с речью когда используешь слова паразиты
↓
ПОСЛЕ: Вот что происходит с речью. Когда используешь слова-паразиты...
```

---

### 3. **Text Formatting** (форматирование текста)

**Название в AssemblyAI:** Text Formatting

**Что делает:**
- Правильные заглавные буквы в начале предложений
- Номера и числа переводит в слова (12 → "двенадцать")
- Убирает двойные пробелы
- Форматирует числовые данные

**Как включить:** Playground → Settings → Text Formatting: ON

**Доступные форматы для скачивания:**
```
✅ Transcript text (.txt) - отформатирован
✅ Paragraphs (.json) - отформатирован
✅ Sentences (.json) - отформатирован
```

**Результат на практике:**
```
ДО:  вот что происходит. когда 2026 год
↓
ПОСЛЕ: Вот что происходит. Когда две тысячи двадцать шестой год
```

---

### 4. **Speaker Labels** (определение спикеров)

**Название в AssemblyAI:** Speaker Labels / Speaker Diarization

**Что делает:**
- Определяет сколько человек говорит в аудио
- Разбивает текст по спикерам (Speaker A, Speaker B и т.д.)
- Показывает кто что говорил
- Идеально для интервью, дискуссий, подкастов

**Как включить:** Playground → Settings → Speaker Labels: ON

**Доступные форматы для скачивания:**
```
✅ Paragraphs (.json) - с информацией спикера
✅ Sentences (.json) - с информацией спикера
✅ Full JSON response - с speaker data
```

**Результат на практике:**
```
[Speaker A] Вот что происходит с речью...
[Speaker B] Да, когда используешь слова-паразиты...
[Speaker A] Правильно! Нужна практика...
```

---

### 5. **Language Detection** (определение языка)

**Название в AssemblyAI:** Language Detection / Automatic Language Detection

**Что делает:**
- Автоматически определяет на каком языке говорит
- Поддерживает русский, украинский и 99+ языков
- Работает если стоит "Auto" вместо ручного выбора

**Как включить:** Playground → Language: Auto (автоматическое определение)

**Доступные форматы для скачивания:**
```
✅ Full JSON response (содержит поле "language_code": "ru")
✅ Metadata с информацией о языке
```

**Результат на практике:**
```
Ты загружаешь аудио → AssemblyAI сам определяет "Russian"
Не нужно выбирать вручную!
```

---

### 6. **Confidence Scores** (уровень уверенности)

**Название в AssemblyAI:** Confidence / Confidence Scores

**Что делает:**
- Показывает насколько уверен AI в распознавании
- Каждое слово/параграф имеет confidence от 0 до 1 (0-100%)
- 0.95 = очень уверен, 0.5 = сомневается

**Как включить:** Автоматически во всех результатах

**Доступные форматы для скачивания:**
```
✅ Paragraphs (.json) - с confidence каждого параграфа
✅ Sentences (.json) - с confidence каждого предложения
✅ Word-level timestamps (.json) - с confidence каждого слова
✅ Full JSON response - со всеми confidence данными
```

**Результат на практике:**
```json
{
  "text": "Вот что происходит",
  "confidence": 0.95,
  "words": [
    {"text": "Вот", "confidence": 0.98},
    {"text": "что", "confidence": 0.97},
    {"text": "происходит", "confidence": 0.91}
  ]
}
```

---

## 🔧 ADVANCED ФУНКЦИИ (Дополнительные - Работают с РУ/УА)

### 7. **Disfluencies** (фильтр слов-паразитов)

**Название в AssemblyAI:** Disfluencies

**Что делает:**
- ✅ **РАБОТАЕТ для русского и украинского!** (в отличие от Filler Words)
- Убирает/выделяет слова-паразиты (ну, типа, короче, вот, блин)
- Убирает звуки-паразиты (эээ, ммм, ааа, хм)
- Может либо удалить, либо отметить их в JSON

**Как включить:** API параметр `disfluencies: true`

**Доступные форматы для скачивания:**
```
✅ Paragraphs (.json) - с отмеченными disfluencies
✅ Sentences (.json) - с отмеченными disfluencies
✅ Word-level timestamps (.json) - с отмеченными disfluencies
✅ Transcript text (.txt) - без паразитов (опционально)
```

**Результат на практике:**
```
ДО:  "Вот, короче, ну, типа, что происходит..."
↓
ПОСЛЕ: "Вот что происходит..."
(или отмечены в JSON как дефлюэнси)
```

**Пример в JSON:**
```json
{
  "paragraphs": [
    {
      "text": "Вот что происходит",
      "words": [
        {"text": "Вот", "type": "filler"},  ← отмечено как паразит
        {"text": "что", "type": "regular"},
        {"text": "происходит", "type": "regular"}
      ]
    }
  ]
}
```

---

### 8. **Topic Detection** (определение тем)

**Название в AssemblyAI:** Topic Detection / Topic Extraction

**Что делает:**
- Автоматически находит основные темы в аудио
- Выделяет о чем говорят (маркетинг, продажи, технология и т.д.)
- Создает список тем без структуры
- Помогает индексировать контент

**Как включить:** Playground → Settings → Topic Detection: ON

**Доступные форматы для скачивания:**
```
✅ Full JSON response (с полем "topics": [...])
✅ Custom export (можешь выбрать только темы)
```

**Результат на практике:**
```json
{
  "topics": [
    {
      "relevance": 0.95,
      "text": "речь и коммуникация"
    },
    {
      "relevance": 0.88,
      "text": "язык и грамматика"
    },
    {
      "relevance": 0.72,
      "text": "публичные выступления"
    }
  ]
}
```

---

### 9. **Sentiment Analysis** (анализ эмоций)

**Название в AssemblyAI:** Sentiment Analysis

**Что делает:**
- Определяет эмоции в речи (позитив, негатив, нейтраль)
- Анализирует тон говорящего
- Присваивает sentiment score каждому параграфу
- Помогает понять реакцию аудитории

**Как включить:** API параметр `sentiment_analysis: true`

**Доступные форматы для скачивания:**
```
✅ Paragraphs (.json) - с sentiment каждого параграфа
✅ Full JSON response - со всеми sentiment данными
```

**Результат на практике:**
```json
{
  "paragraphs": [
    {
      "text": "Это просто замечательно!",
      "sentiment": "POSITIVE",
      "confidence": 0.95
    },
    {
      "text": "Это ужасно и плохо",
      "sentiment": "NEGATIVE",
      "confidence": 0.92
    }
  ]
}
```

---

### 10. **Content Moderation** (модерация контента)

**Название в AssemblyAI:** Content Moderation

**Что делает:**
- Находит мат и оскорбительный контент
- Определяет чувствительный контент
- Помогает отфильтровать неприемлемое
- Редко нужно, но есть

**Как включить:** API параметр `content_moderation: true`

**Доступные форматы для скачивания:**
```
✅ Full JSON response (с flagged контентом)
```

**Результат на практике:**
```json
{
  "paragraphs": [
    {
      "text": "Это... [оскорбительное слово]",
      "moderation_status": "flagged"
    }
  ]
}
```

---

### 11. **Entity Detection** (выделение сущностей)

**Название в AssemblyAI:** Entity Detection

**Что делает:**
- Находит имена, места, организации в тексте
- Выделяет важные понятия
- Помогает структурировать контент

**Как включить:** API параметр `entity_detection: true`

**Доступные форматы для скачивания:**
```
✅ Full JSON response (с entities)
```

**Результат на практике:**
```json
{
  "entities": [
    {"text": "Иван", "type": "PERSON"},
    {"text": "YouTube", "type": "ORGANIZATION"},
    {"text": "Киев", "type": "LOCATION"}
  ]
}
```

---

### 12. **PII Redaction** (защита персональных данных)

**Название в AssemblyAI:** PII Redaction / PII Removal

**Что делает:**
- Находит и скрывает личные данные (номера телефонов, email, имена)
- Заменяет на [PII] или удаляет
- Полезно для privacy-friendly транскриптов

**Как включить:** API параметр `redact_pii: true`

**Доступные форматы для скачивания:**
```
✅ Paragraphs (.json) - с замаскированными PII
✅ Transcript text (.txt) - с замаскированными PII
✅ Full JSON response - с информацией где были PII
```

**Результат на практике:**
```
ДО:  "Позвони мне на +380501234567 или напиши на ivan@example.com"
↓
ПОСЛЕ: "Позвони мне на [PHONE] или напиши на [EMAIL]"
```

---

## 📹 EXPORT ФОРМАТЫ (Что скачивать)

### Доступные форматы для РУ/УА:

```
1. SRT Caption (.srt)
   ├─ Для: YouTube, TikTok, видео
   ├─ Содержит: таймкоды и субтитры
   └─ Пример: 00:00:15,000 --> 00:00:20,000

2. VTT Caption (.vtt)
   ├─ Для: веб-плеер, сайты
   ├─ Содержит: таймкоды и субтитры
   └─ Пример: 00:00:15.000 --> 00:00:20.000

3. Paragraphs (.json)
   ├─ Для: обработка, анализ
   ├─ Содержит: текст, спикера, таймкоды, confidence
   └─ Структура: абзацы

4. Sentences (.json)
   ├─ Для: поиск, индексирование
   ├─ Содержит: текст, спикера, таймкоды
   └─ Структура: предложения (более дробная)

5. Transcript text (.txt)
   ├─ Для: обычные клиенты, архив
   ├─ Содержит: простой текст с спикерами
   └─ Формат: [Speaker A] Текст...

6. Word-level timestamps (.json)
   ├─ Для: видеомонтажеры, синхронизация
   ├─ Содержит: каждое слово с таймкодом
   └─ Точность: мс уровня
```

---

## ❌ ЧТО НЕ РАБОТАЕТ для РУ/УА

| Функция | Почему | Альтернатива |
|---------|--------|---|
| **Filler Words** | Только для EN | Используй `disfluencies: true` |
| **Prompting** | Только U3 Pro (кот. не поддерживает RU/UA) | Используй Claude API после |
| **Translate в Playground** | Экспортируется только оригинал | Используй API `translate_to` |
| **Custom Formatting** | Только через API | Используй API после транскрипции |

---

## 🎯 ФУНКЦИИ ПО СЛУЧАЯМ ИСПОЛЬЗОВАНИЯ

### Для Видеоблогера:
```
✅ Speech-to-Text
✅ Auto Punctuation
✅ Text Formatting
✅ Speaker Labels
✅ Disfluencies (убрать паразиты)

Скачивать:
→ SRT Caption (для YouTube)
→ Transcript text (для архива)
```

### Для Автора Курса:
```
✅ Speech-to-Text
✅ Auto Punctuation
✅ Speaker Labels
✅ Disfluencies
✅ Topic Detection (может быть)

Скачивать:
→ VTT Caption (встроить в курс)
→ Paragraphs JSON (для обработки)
→ Transcript text (как раздаточный материал)
```

### Для Видеомонтажера:
```
✅ Speech-to-Text
✅ Auto Punctuation
✅ Speaker Labels
✅ Disfluencies (найти мусор)

Скачивать:
→ Word-level timestamps (каждое слово с временем)
→ SRT Caption (для финального видео)
```

### Для SEO специалиста:
```
✅ Speech-to-Text
✅ Auto Punctuation
✅ Text Formatting
✅ Topic Detection
✅ Entity Detection (опционально)

Скачивать:
→ Sentences JSON (для индексирования)
→ Paragraphs JSON (для анализа)
```

### Для Разработчика:
```
✅ Speech-to-Text
✅ Language Detection
✅ Confidence Scores
✅ Disfluencies
✅ Sentiment Analysis
✅ Entity Detection

Скачивать:
→ Full JSON response (весь набор данных)
→ Paragraphs JSON (структурированные данные)
```

---

## 📊 ТАБЛИЦА ФУНКЦИЙ (РУ/УА)

| Функция | Включается | Формат | Работает | Цена |
|---------|-----------|--------|---------|------|
| Speech-to-Text | Автоматически | TXT, JSON | ✅ RU/UA | Включено |
| Auto Punctuation | Playground | TXT, JSON | ✅ RU/UA | Включено |
| Text Formatting | Playground | TXT, JSON | ✅ RU/UA | Включено |
| Speaker Labels | Playground | JSON | ✅ RU/UA | Включено |
| Language Detection | Auto mode | JSON | ✅ RU/UA | Включено |
| Confidence Scores | Автоматически | JSON | ✅ RU/UA | Включено |
| Disfluencies | API param | JSON | ✅ RU/UA | Включено |
| Topic Detection | Playground | JSON | ✅ RU/UA | Включено |
| Sentiment Analysis | API param | JSON | ✅ RU/UA | Включено |
| Content Moderation | API param | JSON | ✅ RU/UA | Включено |
| Entity Detection | API param | JSON | ✅ RU/UA | Включено |
| PII Redaction | API param | TXT, JSON | ✅ RU/UA | Включено |
| SRT Export | Playground | .srt | ✅ RU/UA | Включено |
| VTT Export | Playground | .vtt | ✅ RU/UA | Включено |
| **Filler Words** | Playground | JSON | ❌ Только EN | - |
| **Prompting** | API | JSON | ❌ Только U3 Pro | - |
| **Translate** | Playground | TXT | ⚠️ Только preview | - |

---

**ИТОГО для РУ/УА:**
- ✅ 12 функций работают полностью
- ✅ 6 форматов экспорта
- ❌ 3 функции не работают (EN only)

Используй **Universal-2** для всех языков!
