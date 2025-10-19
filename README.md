# PD-модель: автоматизация пайплайна

**Задача.** Реализован сквозной пайплайн: подготовка/валидация данных, обучение с MLflow,
DVC-версии, тесты/CI, REST API на FastAPI, Docker, мониторинг дрифта (PSI).

## Данные
UCI "Default of Credit Card Clients".`data/raw/UCI_Credit_Card.csv` (версируется DVC).

## Быстрый старт
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt

#  dvc init && dvc add data/raw/UCI_Credit_Card.csv
python src/data/make_dataset.py
python src/data/validation.py
python src/models/train.py
```

### MLflow UI
```bash
mlflow ui
```

### DVC
```bash
dvc init
dvc add data/raw/UCI_Credit_Card.csv
dvc repro
```

### API
```bash
uvicorn src.api.app:APP --host 0.0.0.0 --port 8000
```

### Docker
```bash
docker build -t credit-scoring-api .
docker run --rm -p 8000:8000 credit-scoring-api
```

### Тесты и стиль
```bash
pytest -q
flake8
black --check .
```

### Мониторинг дрифта
```bash
python monitor/drift_monitor.py
```

---

## Вариант A (Linux / macOS / Git Bash)

Для удобства в проекте есть **Makefile**, который позволяет запустить весь пайплайн одной командой.

### Запуск всего пайплайна:
```bash
make run-all
```

Команда выполняет:
1. Установку зависимостей  
2. Подготовку и валидацию данных  
3. Обучение модели с логированием в MLflow  
4. Тесты и линтинг  
5. Расчёт метрики дрифта (PSI)

После завершения появится сообщение:
```
✅ Готово! Модель обучена, метрики залогированы, PSI рассчитан.
👉 Запусти API: make run-api  (или)  uvicorn src.api.app:APP --host 0.0.0.0 --port 8000
```

### Дополнительные команды:
```bash
make run-api       # запуск REST API
make mlflow-ui     # интерфейс MLflow
make dvc-init      # инициализация DVC
make dvc-repro     # прогон DVC пайплайна
make docker-build  # сборка Docker-образа
make docker-run    # запуск контейнера
make clean         # очистка артефактов (data/processed, models, reports, mlruns)
```

---

## Вариант B (Windows PowerShell)

Если используется Windows без утилиты `make`, можно воспользоваться скриптом **`run_all.ps1`**.

Он выполняет все шаги автоматически:
- установку зависимостей  
- подготовку и валидацию данных  
- обучение модели  
- тестирование и проверку стиля  
- расчёт дрифта PSI

### Запуск:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

.\run_all.ps1

```

После завершения появится сообщение:
```
✅ Готово! Модель обучена, метрики залогированы, PSI рассчитан.
👉 Запуск API: uvicorn src.api.app:APP --host 0.0.0.0 --port 8000
```

Таким образом, весь процесс — от подготовки данных до финального обучения и расчёта метрик — можно выполнить **одной командой**.

