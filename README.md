# Қауіпсіз Қадам — Flask + AI + Railway

Жасөспірімдерге арналған қауіпсіздік платформасы. Жоба рөлдік авторизацияны, өтініштерді, тесттерді, жетекшіге хабарлама жіберуді және Ollama арқылы қазақша AI навигаторын қамтиды.

## Негізгі мүмкіндіктер

- Оқушы / ата-ана / мұғалім рөлдері
- Оқушы тек өз өтініштерін көреді
- Ата-ана тек байланыстырылған баланың өтініштерін көреді
- Мұғалім барлық өтініштерді көреді
- Тіркелмей тез өтініш жіберу
- Құқықтық және қауіпсіздік тесттері
- Жетекшіге хабарлама
- Қазақша AI навигатор — Ollama `/api/chat`
- Local SQLite немесе Railway PostgreSQL
- Railway үшін Gunicorn + healthcheck дайын

## Демо аккаунттар

- Оқушы: `student` / `student123`
- Ата-ана: `parent` / `parent123`
- Мұғалім: `teacher` / `teacher123`

Өндірістік ортада `SEED_DEMO=0` орнатуға болады.

## Windows-та жергілікті іске қосу

### 1. Ollama моделін тексеру

Сізде қолданылған модель:

```cmd
ollama run hf.co/mradermacher/Qwen3.5-4B-Kazakh-GGUF:Q4_K_M
```

Ollama сервері әдетте мына жерде жұмыс істейді:

```text
http://127.0.0.1:11434
```

### 2. Python ортасы

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Сайт:

```text
http://127.0.0.1:5000
```

Ескерту: `.env` файлын Flask автоматты түрде оқымайды. Windows-та айнымалыларды `set` арқылы беруге немесе IDE/Railway Variables бөлімінде орнатуға болады. Жергілікті әдепкі мәндер Ollama үшін дайын.

## AI баптаулары

Қолданылатын айнымалылар:

```text
AI_ENABLED=1
AI_BASE_URL=http://127.0.0.1:11434
AI_MODEL=hf.co/mradermacher/Qwen3.5-4B-Kazakh-GGUF:Q4_K_M
AI_TIMEOUT=90
```

Backend `think: false` параметрін жібереді, сондықтан пайдаланушыға Thinking/Reasoning мәтіні көрсетілмеуі тиіс.

AI күйін тексеру:

```text
GET /api/ai/status
```

## Railway-ге жүктеу

1. Осы папканы GitHub репозиторийіне жүктеңіз.
2. Railway → New Project → Deploy from GitHub Repo.
3. PostgreSQL сервисін қосыңыз.
4. Web service-ке PostgreSQL `DATABASE_URL` айнымалысын қосыңыз/байланыстырыңыз.
5. Variables ішінде кемінде мыналарды орнатыңыз:

```text
SECRET_KEY=өте-ұзын-кездейсоқ-құпия-сөз
SEED_DEMO=1
SESSION_COOKIE_SECURE=1
AI_ENABLED=1
AI_BASE_URL=https://СІЗДІҢ_AI_СЕРВЕР
AI_MODEL=hf.co/mradermacher/Qwen3.5-4B-Kazakh-GGUF:Q4_K_M
AI_TIMEOUT=120
```

`railway.toml` және `Procfile` Gunicorn іске қосуға дайын.

## Маңызды: Ollama және Railway

Railway-дегі сайт `127.0.0.1:11434` арқылы сіздің үй компьютеріңіздегі Ollama-ны көрмейді. Railway-ге шығарғанда `AI_BASE_URL` интернеттен қолжетімді Ollama/API серверіне бағытталуы керек.

Яғни архитектура:

```text
Пайдаланушы → Railway Flask → AI_BASE_URL → Ollama + Kazakh model
```

Жергілікті тест кезінде:

```text
Пайдаланушы → localhost Flask → localhost:11434 Ollama
```

Сайт кодын қайта жазудың қажеті жоқ — тек `AI_BASE_URL` өзгереді.

## Healthcheck

```text
GET /health
```

Railway осы endpoint-ті қолданады.

## Қауіпсіздік

- Продакшнда `SECRET_KEY` міндетті түрде ауыстырыңыз.
- Демо аккаунттарды нақты қолданушыларға қалдырмаңыз.
- AI жауабы кәсіби заңгерлік/медициналық кеңестің орнына жүрмейді.
