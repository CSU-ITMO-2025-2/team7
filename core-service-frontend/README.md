# Core Service Frontend

React приложение для работы с Core Service API.

## Возможности

- Регистрация и авторизация пользователей
- Создание запусков (runs) с указанием dataset_id и конфигурации
- Просмотр списка созданных запусков с их статусами
- Современный и чистый UI

## Технологии

- React 18
- React Router DOM
- Vite
- CSS Modules

## Структура проекта

```
src/
├── components/          # Переиспользуемые компоненты
│   ├── Alert/
│   ├── Button/
│   ├── Card/
│   ├── Input/
│   ├── Layout/
│   └── ProtectedRoute/
├── context/            # React Context (AuthContext)
├── pages/              # Страницы приложения
│   ├── Home/
│   ├── Login/
│   └── Register/
├── services/           # API сервисы
│   └── api.js
├── App.jsx             # Главный компонент с роутингом
└── main.jsx            # Точка входа
```

## Разработка

1. Установите зависимости:
   ```bash
   npm install
   ```

2. Создайте файл `.env` на основе `.env.example`:
   ```bash
   cp .env.example .env
   ```

3. Запустите dev сервер:
   ```bash
   npm run dev
   ```

4. Откройте браузер по адресу `http://localhost:3000`

## Сборка

```bash
npm run build
```

Собранные файлы будут в директории `dist/`.

## Docker

Для сборки и запуска через Docker:

```bash
docker build -t core-service-frontend .
docker run -p 80:80 core-service-frontend
```

Или используйте docker-compose из корня проекта.

## API

Приложение ожидает, что Core Service API доступен по адресу, указанному в `VITE_API_BASE` (по умолчанию `http://localhost:8000`).

### Эндпоинты

- `POST /auth/register` - регистрация пользователя
- `POST /auth/login` - авторизация и получение токена
- `POST /runs` - создание нового запуска
- `GET /runs` - получение списка запусков пользователя

Токен сохраняется в `localStorage` под ключом `coreServiceToken`.
