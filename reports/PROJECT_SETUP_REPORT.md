# Отчет по настройке проекта Boston Housing IPML

**Автор:** datanalist@github.com  
**Дата:** 24 ноября 2025  
**Проект:** ipml-boston-housing  
**Python:** 3.13  

---

## 📋 Оглавление

1. [Структура проекта (2 балла)](#1-структура-проекта)
2. [Качество кода (2 балла)](#2-качество-кода)
3. [Управление зависимостями (2 балла)](#3-управление-зависимостями)
4. [Git workflow (1 балл)](#4-git-workflow)
5. [Подробная история bash-команд (Debian)](#5-подробная-история-bash-команд-debian)

---

## 1. Структура проекта

### ✅ Задача: Создать структуру папок с помощью Cookiecutter

**Команды для инициализации проекта с нуля:**

```bash
# 1. Установка Python 3.13 через uv
uv python install 3.13

# 2. Инициализация проекта
uv init --python=3.13

# 3. Создание виртуального окружения
uv venv .venv --python=3.13

# 4. Установка Cookiecutter Data Science
uv add cookiecutter-data-science

# 5. Запуск генератора структуры
uv run ccds
```

**Результат выполнения:**

```
✓ Installed Python 3.13.9 in 35.86s
✓ Initialized project `ipml-boston-housing`
✓ Creating virtual environment at: .venv
✓ Installed 24 packages (cookiecutter-data-science==2.3.0)
✓ Project structure created
```

**Параметры конфигурации CCDS:**
- Python Version: 3.13
- Environment Manager: uv
- Dependency File: pyproject.toml
- Testing Framework: pytest
- Linting: ruff
- Docs: mkdocs

**Созданная структура:**

```
ipml_boston_housing/
├── data/                      # raw, processed, interim, external
├── docs/                      # MkDocs документация
├── models/                    # Сохраненные ML модели
├── notebooks/                 # Jupyter notebooks
├── reports/figures/           # Графики
├── src/                       # Исходный код
│   ├── config.py
│   ├── dataset.py
│   ├── features.py
│   ├── plots.py
│   └── modeling/
│       ├── train.py
│       └── predict.py
├── tests/test_data.py         # Тесты
├── docker/Dockerfile
├── Makefile
├── pyproject.toml
└── README.md
```

### ✅ Задача: Создать README с описанием проекта

**Результат:** README.md содержит описание проекта, датасета (13 признаков + MEDV), инструкции по установке, структуру проекта и доступные команды Makefile.


---

## 2. Качество кода

### ✅ Задача: Настроить pre-commit hooks, форматирование и линтеры

**Команды:**

```bash
# 1. Установка инструментов
uv add ruff
uv add pre-commit

# 2. Инициализация pre-commit
uv run pre-commit install
```

**Результат выполнения:**

```
✓ ruff==0.14.6 installed
✓ pre-commit==4.5.0 installed (+ 8 dependencies)
✓ Pre-commit hooks activated
✓ Environment for ruff-pre-commit initialized
```

**Созданные файлы:**

**`.pre-commit-config.yaml`:**
```yaml
repos:
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.14.6
  hooks:
    - id: ruff-check
      types_or: [python, pyi]
      args: [--fix]
    - id: ruff-format
      types_or: [python, pyi]
```

**`Makefile` (команды):**
```makefile
lint:
	ruff format --check
	ruff check

format:
	ruff check --fix
	ruff format
```

**`.python-version`:**
```
3.13
```

**Доступные команды:**
```bash
make lint       # Проверка кода
make format     # Форматирование
make test       # Тесты
make clean      # Очистка
```

---

## 3. Управление зависимостями

### ✅ Задача: Настроить пакетный менеджер, pyproject.toml, виртуальное окружение, Dockerfile

**Команды:**

```bash
# 1. Установка Python и создание окружения (выполнено выше)
uv python install 3.13
uv init --python=3.13
uv venv .venv --python=3.13

# 2. Активация окружения
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# 3. Установка зависимостей
uv add cookiecutter-data-science>=2.3.0
uv add pre-commit>=4.5.0
uv add ruff>=0.14.6

# 4. Синхронизация
uv sync
```

**Результат выполнения:**

```
✓ uv package manager configured
✓ Python 3.13.9 installed
✓ Virtual environment .venv created
✓ 35 packages installed (including transitive dependencies)
✓ uv.lock created with SHA256 hashes
✓ docker/Dockerfile created
```

**`pyproject.toml`:**
```toml
[project]
name = "ipml-boston-housing"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "cookiecutter-data-science>=2.3.0",
    "pre-commit>=4.5.0",
    "ruff>=0.14.6",
]
```

**Файл блокировки:**
- `uv.lock` - 35 пакетов с точными версиями и хэшами
- Гарантирует воспроизводимые сборки

**Docker:**
- Файл `docker/Dockerfile` создан и готов к настройке


---

## 4. Git workflow

### ✅ Задача: Настроить Git, создать .gitignore, настроить ветки

**Команды:**

```bash
# 1. Конфигурация Git
git config --global user.name "Mikhail M."
git config --global user.email "datanalist@github.com"

# 2. Инициализация репозитория и коммиты
git init
git add .
git commit -m "Initial commit"
git commit -m "init"
git commit -m "add dockerfile"
git commit -m "init pre-commit"

# 3. Создание веток
git branch dev
git branch dev-clearml
git branch dev-dagster
git branch dev-dvc
git branch dev-mlflow
git branch research
git branch rsch-eda
git branch rsch-feature_engineering
git branch rsch-models

# 4. Push в remote
git push origin --all
```

**Результат выполнения:**

```
✓ Git user configured
✓ 4 commits created
✓ .gitignore created (214 rules for ML projects)
✓ 10 branches created and pushed to remote
```

**История коммитов:**

```
* c31b844 init pre-commit
* 17d2fb3 add dockerfile
* ea88be7 init
* 2db4087 Initial commit
```

**Структура веток:**

```
main (production)
  └── dev (development)
       ├── dev-clearml    # ClearML tracking
       ├── dev-dagster    # Orchestration
       ├── dev-dvc        # Data versioning
       └── dev-mlflow     # MLflow tracking

research (experiments)
  ├── rsch-eda                    # EDA
  ├── rsch-feature_engineering    # Feature engineering
  └── rsch-models                 # Model training
```

**`.gitignore` (основные секции):**

```gitignore
# ML files
models/
data/

# Python
__pycache__/
*.py[cod]
.venv/

# IDE
.vscode/
.idea/

# Jupyter
.ipynb_checkpoints/
```

**Всего:** 214 строк правил

---

## 🚀 Быстрый старт (все команды)

```bash
# Полная инициализация проекта с нуля
uv python install 3.13
uv init --python=3.13
uv venv .venv --python=3.13
source .venv/bin/activate

# Установка инструментов
uv add cookiecutter-data-science
uv add ruff pre-commit

# Создание структуры
uv run ccds

# Настройка Git
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
git init
git add .
git commit -m "Initial commit"

# Инициализация pre-commit
uv run pre-commit install

# Создание веток
git branch dev
git branch research

# Проверка
make lint
make test
```

---

## 5. Подробная история bash-команд (Debian)
```bash
soho@Sohobook:~/ipml_boston_housing$ history
  1  sudo apt update
  2  sudo apt install git
  3  git clone git@github.com:datanalist/ipml_boston_housing.git
  4  ls -al ~/.ssh
  5  ssh-keygen -t ed25519 -C "secret"
  6  ssh-keygen -t ed25519 -C "secret"
  7  eval "$(ssh-agent -s)"
  8  ssh-add ~/.ssh/id_ed25519
  9  cat ~/.ssh/id_ed25519.pub
  10  ssh -T git@github.com
  11  uv
  12  curl -LsSf https://astral.sh/uv/install.sh | sh
  13  snap
  14  apt install snap
  15  sudo apt install snap
  16  sudo snap install astral-uv --classic
  17  sudo apt update
  18  snap
  19  snapd
  20  sudo reboot
  21  snap
  22  sudo snap install snapd
  23  sudo snap install hello-world
  24  sudo snap install astral-uv --classic
  25  uv
  26  astral-uv
  27  astral-uv.uv
  28  sudo reboot
  29  uv
  30  git clone git@github.com:datanalist/ipml_boston_housing.git
  31  uv init
  32  uv add cookiecutter-data-science
  33  ccds
  34  uv run ccds
  35  git clone git@github.com:datanalist/ipml_boston_housing.git
  36  uv init
  37  uv python install 3.13
  38  uv python list
  39  uv venv python 3.13
  40  uv venv 
  41  uv venv --help
  42  uv venv .venv --python=python3.13
  43  uv run python --version
  44  uv venv .venv --python=python3.13
  45  uv run python --version
  46  uv init
  47  uv init --python=3.13
  48  uv init
  49  uv venv .venv --python=3.13
  50  uv run python --version
  51  uv add cookiecutter-data-science
  52  uv run ccds
  53  git config --global user.name "Mikhail M."
  54  git config --global user.email "datanalist@github.com"
  55  uv add ruff
  56  uv add pre-commit
  57  uv run pre-commit
```


**Отчет подготовлен:** 24.11.2025 Макаровым М.В. совместно с AI\
**Проект:** ipml-boston-housing
