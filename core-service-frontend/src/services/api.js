const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
const ARTIFACTS_BASE = import.meta.env.VITE_ARTIFACTS_BASE || 'http://localhost:8001';

const getAuthHeaders = () => {
  const token = localStorage.getItem('coreServiceToken');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const authService = {
  async register(login, password) {
    const response = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ login, password }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Не удалось зарегистрировать пользователя');
    }

    return response.json();
  },

  async login(login, password) {
    const formData = new URLSearchParams();
    formData.append('username', login);
    formData.append('password', password);

    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Неверные учётные данные');
    }

    const data = await response.json();
    localStorage.setItem('coreServiceToken', data.access_token);
    return data;
  },

  async getCurrentUser() {
    const response = await fetch(`${API_BASE}/auth/me`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Не удалось получить информацию о пользователе');
    }

    return response.json();
  },

  logout() {
    localStorage.removeItem('coreServiceToken');
  },

  getToken() {
    return localStorage.getItem('coreServiceToken');
  },

  isAuthenticated() {
    return Boolean(this.getToken());
  },
};

export const datasetsService = {
  async uploadDataset(name, file) {
    const headers = getAuthHeaders();
    if (!headers.Authorization) {
      throw new Error('Требуется авторизация');
    }

    const formData = new FormData();
    formData.append('dataset_name', name);
    formData.append('file', file);

    const response = await fetch(`${ARTIFACTS_BASE}/datasets`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Не удалось загрузить датасет');
    }

    return response.json();
  },

  async getDatasets() {
    const headers = getAuthHeaders();
    if (!headers.Authorization) {
      throw new Error('Требуется авторизация');
    }

    const response = await fetch(`${ARTIFACTS_BASE}/datasets`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Не удалось получить список датасетов');
    }

    return response.json();
  },
};

export const runsService = {
  async createRun(datasetId, configuration = {}) {
    const response = await fetch(`${API_BASE}/runs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
      body: JSON.stringify({
        dataset_id: datasetId,
        configuration,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Не удалось создать запуск');
    }

    return response.json();
  },

  async getRuns() {
    const response = await fetch(`${API_BASE}/runs`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Не удалось получить список запусков');
    }

    return response.json();
  },

  async getRun(runId) {
    const response = await fetch(`${API_BASE}/runs/${runId}`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Не удалось получить запуск');
    }

    return response.json();
  },
};
