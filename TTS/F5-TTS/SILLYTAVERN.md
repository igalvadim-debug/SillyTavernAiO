# F5-TTS + SillyTavern

Сервер `f5_tts.serve_openai` отдаёт **OpenAI-совместимый** эндпоинт `/v1/audio/speech`,
который понимает встроенный в SillyTavern провайдер TTS **«OpenAI Compatible»**.

Голос клонируется zero-shot из сохранённого референс-клипа (см. раздел «Голоса»).
По умолчанию используется русская модель `Misha24-10/F5-TTS_RUSSIAN`.

## 1. Сохранить голос

1. Запусти `start.bat` → **1** (Gradio Web UI).
2. Загрузи **Reference Audio** (чистый клип ~3–10 с) и впиши **Reference Text** — точную расшифровку.
3. В строке «Save current Reference Audio/Text as a new voice — name» задай имя и нажми **Save voice**.
4. Голос появится в выпадающем списке **Voice preset** и в папке `F5-TTS/voices/`.

## 2. Запустить API-сервер

`start.bat` → **4** (порт **7868**), либо вручную:

```bat
venv\Scripts\activate
python -m f5_tts.serve_openai --port 7868
```

Проверка:

```bat
curl http://127.0.0.1:7868/v1/audio/voices
curl -o out.mp3 -X POST http://127.0.0.1:7868/v1/audio/speech ^
  -H "Content-Type: application/json" ^
  -d "{\"input\":\"Привет, это проверка.\",\"voice\":\"example_en\"}"
```

## 3. Настроить SillyTavern

Открой **Extensions → TTS**, выбери провайдер **«OpenAI Compatible»** и заполни:

| Поле | Значение |
|------|----------|
| API Endpoint / Base URL | `http://127.0.0.1:7868/v1/audio/speech` |
| Model | `f5-tts` |
| API Key | любой (например `sk-local`) |
| Voice | имя голоса из `voices/` (например `example_en`), либо оставь пустым — возьмётся голос по умолчанию |
| Response format | `mp3` (сервер также отдаёт `wav`) |
| Speed | 1.0 (пробрасывается в F5-TTS) |

Список голосов можно получить из `GET /v1/audio/voices`; в поле Voice можно вписать любое имя из этого списка.

## Дополнительно

- **Качество/скорость**: `nfe_step` — число шагов сэмплера: больше = чище, но медленнее.
  Лончеры (`start_f5_solo.bat`, `start.bat`, `start_silly.bat`) передают `--nfe-step 11`.
  Меньше (`8`) — быстрее, но больше артефактов; больше (`16`–`32`) — чище, но медленнее.
  В отдельном запросе можно переопределить полем `"nfe_step"`.
- **Окончания слов**: F5 оценивает длину фразы заранее и иногда обрезает последнюю
  фонему. `--length-pad` (или поле `"length_scale"` в запросе) добавляет запас:
  `1.0` — как раньше, `1.06` (по умолчанию) — заметно мягче, `1.12`–`1.2` — концовка
  затухает в тишину. Больше запас — чуть длиннее/медленнее звучит фраза.
- **Переопределить модель**: флаги `--ckpt`, `--vocab`, `--model`, `--nfe-step`,
  `--length-pad`, `--device`, `--host`, `--port`, `--no-warmup`.
- **Эндпоинты**: `POST /v1/audio/speech`, `GET /v1/models`, `GET /v1/audio/voices`, `GET /health`.
- **Голоса** лежат в `F5-TTS/voices/` — файлы `<имя>.wav` и индекс `voices.json`
  (`{"default": <имя>, "voices": {<имя>: {"file": ..., "ref_text": ...}}}`).
