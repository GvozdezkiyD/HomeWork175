# ================================================================
# Автоматический пайплайн PD-модели (PowerShell 7+)
# Версия: 3.0 — авто-venv, PYTHONPATH, DVC, Docker, проверка API
# ================================================================

# ---------- НАСТРОЙКИ ----------
$WITH_DVC        = $true     # прогон dvc init/add/repro
$WITH_DOCKER     = $true     # docker build
$RUN_CONTAINER   = $false    # запустить контейнер после сборки (если true — ещё и проверим /predict)
$CHECK_API_LOCAL = $true     # проверить локальный FastAPI через uvicorn (без Docker)
$MLFLOW_UI_HINT  = $true     # просто напомнить команду mlflow ui
# --------------------------------------------------------

$env:PYTHONPATH = "$PSScriptRoot"
$ErrorActionPreference = "Stop"
Write-Host "`n🚀 Запуск полного пайплайна PD-модели..." -ForegroundColor Yellow

# --- Проверка и активация виртуальной среды ---
$venvPath = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    if (-not $env:VIRTUAL_ENV) {
        Write-Host "Активируем виртуальную среду..." -ForegroundColor Cyan
        & $venvPath
    }
} else {
    Write-Host "Виртуальная среда не найдена. Создаю..." -ForegroundColor Yellow
    python -m venv .venv
    & ".\.venv\Scripts\Activate.ps1"
}

# --- Делаем src/ пакетом, чтобы import src.* работал всегда ---
New-Item -ItemType File -Path "src\__init__.py" -Force | Out-Null
New-Item -ItemType File -Path "src\data\__init__.py" -Force | Out-Null
New-Item -ItemType File -Path "src\features\__init__.py" -Force | Out-Null
New-Item -ItemType File -Path "src\models\__init__.py" -Force | Out-Null
New-Item -ItemType File -Path "src\api\__init__.py" -Force | Out-Null

# --- Проверим наличие исходного CSV ---
if (-not (Test-Path "data\raw\UCI_Credit_Card.csv")) {
    Write-Host "❌ Не найден data\raw\UCI_Credit_Card.csv. Положи файл и запусти снова." -ForegroundColor Red
    exit 1
}

# --- Обновление pip/setuptools/wheel ---
Write-Host "`n1) Обновление инструментов..." -ForegroundColor Cyan
python -m pip install --upgrade pip setuptools wheel

# --- Установка зависимостей проекта ---
Write-Host "`n2) Установка зависимостей из requirements.txt..." -ForegroundColor Cyan
try {
    python -m pip install -r requirements.txt
} catch {
    Write-Host "⚠️  Проблема с бинарями. Ставлю готовые колёса pandas/numpy и докатываю остальное..." -ForegroundColor Yellow
    python -m pip install --only-binary=:all: pandas numpy
    python -m pip install -r requirements.txt --no-deps
}

# --- Подготовка данных ---
Write-Host "`n3) Подготовка датасета..." -ForegroundColor Cyan
python src/data/make_dataset.py

# --- Валидация данных (Pandera/GE — в файле validation.py как настроишь) ---
Write-Host "`n4) Валидация данных..." -ForegroundColor Cyan
try {
    if (Test-Path "src\data\validation.py") {
        python src/data/validation.py
    } else {
        Write-Host "❌ Не найден файл src\data\validation.py" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Валидация упала. Смотри отчёты в data/expectations/*.json" -ForegroundColor Red
    exit 1
}

# --- Мелкий патч train.py: artifact_path -> name (убрать WARNING MLflow) ---
$trainPath = "src\models\train.py"
if (Test-Path $trainPath) {
    $content = Get-Content $trainPath -Raw
    if ($content -match "artifact_path\s*=") {
        $content = $content -replace "artifact_path\s*=", "name="
        Set-Content $trainPath $content -Encoding UTF8
        Write-Host "ℹ️  Обновил MLflow логирование модели: artifact_path -> name" -ForegroundColor DarkCyan
    }
}

# --- Обучение модели и логирование (MLflow) ---
Write-Host "`n5) Обучение модели и логирование в MLflow..." -ForegroundColor Cyan
python src/models/train.py

# --- Юнит-тесты и стиль ---
Write-Host "`n6) Запуск тестов и проверка кода..." -ForegroundColor Cyan
$testsOk = $true
try {
    pytest -q
    flake8
    black --check .
} catch {
    $testsOk = $false
    Write-Host "⚠️  Проверка кода/тесты вернули предупреждения или ошибки. Продолжаю пайплайн." -ForegroundColor Yellow
}

# --- Мониторинг дрифта ---
Write-Host "`n7) Расчёт метрики дрифта PSI..." -ForegroundColor Cyan
python monitor/drift_monitor.py

# --- DVC: init / add / repro ---
if ($WITH_DVC) {
    Write-Host "`n8) DVC пайплайн..." -ForegroundColor Cyan
    if (-not (Test-Path ".dvc")) {
        dvc init
    }
    if (-not (Test-Path "data\raw\UCI_Credit_Card.csv.dvc")) {
        dvc add data/raw/UCI_Credit_Card.csv
    }
    dvc repro
}

# --- Docker: build (run и проверка /predict) ---
if ($WITH_DOCKER) {
    Write-Host "`n9) Docker сборка образа..." -ForegroundColor Cyan
    docker build -t credit-scoring-api .
    if ($RUN_CONTAINER) {
        Write-Host "Запускаю контейнер на 8000..." -ForegroundColor Cyan
        $cid = (docker run -d -p 8000:8000 credit-scoring-api).Trim()
        Start-Sleep -Seconds 4

        # проверка POST /predict
        try {
            $body = @{
              limit_bal = 200000
              sex = 1
              education = 2
              marriage = 1
              age = 35
              pay_1 = 0
              bill_amt1 = 5000
              pay_amt1 = 2000
            } | ConvertTo-Json
            $resp = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/predict" -ContentType "application/json" -Body $body
            Write-Host "✅ Ответ контейнера /predict: $($resp | ConvertTo-Json -Depth 5)" -ForegroundColor Green
        } catch {
            Write-Host "❌ Не удалось получить ответ от контейнера /predict" -ForegroundColor Red
        } finally {
            if ($cid) { docker stop $cid | Out-Null }
        }
    } else {
        Write-Host "Пропущен автозапуск контейнера (RUN_CONTAINER=false). Запусти вручную при желании:" -ForegroundColor DarkGray
        Write-Host "docker run --rm -p 8000:8000 credit-scoring-api" -ForegroundColor DarkGray
    }
}

# --- Проверка локального API через uvicorn ---
if ($CHECK_API_LOCAL) {
    Write-Host "`n10) Быстрая проверка локального API (без Docker)..." -ForegroundColor Cyan
    Write-Host "Запускать uvicorn в фоне не буду, чтобы не блокировать скрипт." -ForegroundColor DarkGray
    Write-Host "Если нужно — выполни отдельно: uvicorn src.api.app:APP --host 0.0.0.0 --port 8000" -ForegroundColor DarkGray
}

# --- Финальные подсказки ---
Write-Host "`n✅ Готово! Модель обучена, метрики залогированы, PSI рассчитан." -ForegroundColor Green
if ($MLFLOW_UI_HINT) {
    Write-Host "👉 MLflow UI: mlflow ui" -ForegroundColor Yellow
}
Write-Host "👉 Запуск API локально: uvicorn src.api.app:APP --host 0.0.0.0 --port 8000" -ForegroundColor Yellow
Write-Host "👉 Docker: docker run --rm -p 8000:8000 credit-scoring-api" -ForegroundColor Yellow
Write-Host "`n===============================================================" -ForegroundColor DarkGray