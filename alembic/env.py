import sys
import importlib.util
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Загружаем модули из обоих сервисов напрямую из файлов
here = Path(__file__).parent.parent

core_service_path = here / "core-service"
artifacts_service_path = here / "artifacts-service"

def load_module_from_file(file_path: Path, parent_path: Path):
    """Загружает модуль из файла с правильной настройкой для относительных импортов"""
    module_name = f"app.{file_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {module_name} from {file_path}")
    
    parent_str = str(parent_path)
    was_in_path = parent_str in sys.path
    if not was_in_path:
        sys.path.insert(0, parent_str)
    
    try:
        module = importlib.util.module_from_spec(spec)
        module.__package__ = "app"
        module.__name__ = module_name
        
        # Регистрируем модуль в sys.modules
        sys.modules[module_name] = module
        
        spec.loader.exec_module(module)
        return module
    finally:
        if not was_in_path and parent_str in sys.path:
            sys.path.remove(parent_str)

# Загружаем модули core-service в правильном порядке
core_app_path = core_service_path / "app"
sys.path.insert(0, str(core_service_path))

# Объявляем переменные для ссылок на модули
core_config_ref = None
core_database_ref = None
core_models_ref = None

try:
    # Создаем пустой модуль app
    if "app" not in sys.modules:
        app_module = type(sys)("app")
        app_module.__package__ = "app"
        app_module.__name__ = "app"
        app_module.__path__ = [str(core_app_path)]
        sys.modules["app"] = app_module
    
    # Загружаем в правильном порядке: config -> database -> models
    core_config = load_module_from_file(core_app_path / "config.py", core_service_path)
    core_database = load_module_from_file(core_app_path / "database.py", core_service_path)
    core_models = load_module_from_file(core_app_path / "models.py", core_service_path)
    
    # Сохраняем ссылки на модули core-service перед загрузкой artifacts-service
    core_config_ref = core_config
    core_database_ref = core_database
    core_models_ref = core_models
finally:
    if str(core_service_path) in sys.path:
        sys.path.remove(str(core_service_path))

# Загружаем модули artifacts-service
artifacts_app_path = artifacts_service_path / "app"
sys.path.insert(0, str(artifacts_service_path))

# Объявляем переменную для ссылки на artifacts_database
artifacts_database_ref = None

try:
    # Пересоздаем модуль app для artifacts-service
    app_module = type(sys)("app")
    app_module.__package__ = "app"
    app_module.__name__ = "app"
    app_module.__path__ = [str(artifacts_app_path)]
    sys.modules["app"] = app_module
    
    # Загружаем в правильном порядке: config -> database -> models
    
    # Очищаем sys.modules от предыдущих модулей app.* перед загрузкой artifacts-service
    keys_to_remove = [k for k in sys.modules.keys() if k.startswith("app.")]
    for k in keys_to_remove:
        del sys.modules[k]
    
    artifacts_config = load_module_from_file(artifacts_app_path / "config.py", artifacts_service_path)
    artifacts_database = load_module_from_file(artifacts_app_path / "database.py", artifacts_service_path)
    artifacts_models = load_module_from_file(artifacts_app_path / "models.py", artifacts_service_path)
    
    # Сохраняем ссылку на artifacts_database
    artifacts_database_ref = artifacts_database
finally:
    if str(artifacts_service_path) in sys.path:
        sys.path.remove(str(artifacts_service_path))

# Получаем Base и settings из сохраненных ссылок
CoreBase = core_database_ref.Base
ArtifactsBase = artifacts_database_ref.Base
settings = core_config_ref.settings

# Объединяем метаданные из обоих Base
from sqlalchemy import MetaData

# Создаем новое MetaData и добавляем таблицы из обоих Base
target_metadata = MetaData()

# Добавляем таблицы из CoreBase
for table in CoreBase.metadata.tables.values():
    # Копируем таблицу в новое метаданное
    table.tometadata(target_metadata)

# Добавляем таблицы из ArtifactsBase
for table in ArtifactsBase.metadata.tables.values():
    # Копируем таблицу в новое метаданное
    table.tometadata(target_metadata)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

sync_url = settings.postgres.async_url.replace("+psycopg_async", "").replace("postgresql+asyncpg", "postgresql+psycopg")
config.set_main_option("sqlalchemy.url", sync_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    async_url = settings.postgres.async_url
    connectable = async_engine_from_config(
        {"sqlalchemy.url": async_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    import asyncio

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
