import { useState, useEffect } from 'react';
import { datasetsService, authService } from '../../services/api';
import { Input } from '../../components/Input/Input';
import { Button } from '../../components/Button/Button';
import { Alert } from '../../components/Alert/Alert';
import { Card } from '../../components/Card/Card';
import './Datasets.css';

export const Datasets = () => {
  const [datasets, setDatasets] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingDatasets, setIsLoadingDatasets] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [datasetName, setDatasetName] = useState('');
  const [file, setFile] = useState(null);
  const [userId, setUserId] = useState(null);

  useEffect(() => {
    loadUserAndDatasets();
  }, []);

  const loadUserAndDatasets = async () => {
    try {
      const user = await authService.getCurrentUser();
      setUserId(user.id);
      await loadDatasets(user.id);
    } catch (err) {
      setError('Не удалось загрузить информацию о пользователе: ' + err.message);
      setIsLoadingDatasets(false);
    }
  };

  const loadDatasets = async (uid) => {
    setIsLoadingDatasets(true);
    try {
      const data = await datasetsService.getDatasets(uid);
      setDatasets(data);
    } catch (err) {
      setError('Не удалось загрузить список датасетов: ' + err.message);
    } finally {
      setIsLoadingDatasets(false);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        setError('Пожалуйста, выберите CSV файл');
        setFile(null);
        return;
      }
      setFile(selectedFile);
      setError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!datasetName.trim()) {
      setError('Введите название датасета');
      return;
    }

    if (!file) {
      setError('Выберите CSV файл');
      return;
    }

    if (!userId) {
      setError('Не удалось определить пользователя');
      return;
    }

    setIsLoading(true);
    try {
      const dataset = await datasetsService.uploadDataset(datasetName, file, userId);
      setSuccess(`Датасет "${dataset.name}" успешно загружен`);
      setDatasetName('');
      setFile(null);
      // Reset file input
      const fileInput = document.getElementById('file-input');
      if (fileInput) fileInput.value = '';
      await loadDatasets(userId);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('ru-RU');
  };

  return (
    <div className="datasets">
      <section className="datasets-section">
        <h2 className="section-title">Загрузить датасет</h2>
        <Card>
          {error && (
            <Alert variant="error" onClose={() => setError('')}>
              {error}
            </Alert>
          )}
          {success && (
            <Alert variant="success" onClose={() => setSuccess('')}>
              {success}
            </Alert>
          )}
          <form onSubmit={handleSubmit}>
            <Input
              label="Название датасета"
              type="text"
              value={datasetName}
              onChange={(e) => setDatasetName(e.target.value)}
              required
              placeholder="Введите название датасета"
            />
            <div className="input-group">
              <label className="input-label">CSV файл</label>
              <input
                id="file-input"
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="file-input"
                required
              />
              {file && <div className="file-name">Выбран: {file.name}</div>}
            </div>
            <div className="form-actions">
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Загрузка...' : 'Загрузить датасет'}
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => userId && loadDatasets(userId)}
                disabled={isLoadingDatasets || !userId}
              >
                Обновить список
              </Button>
            </div>
          </form>
        </Card>
      </section>

      <section className="datasets-section">
        <h2 className="section-title">Мои датасеты</h2>
        {isLoadingDatasets ? (
          <Card>
            <div className="loading">Загрузка...</div>
          </Card>
        ) : datasets.length === 0 ? (
          <Card>
            <div className="empty-state">Датасетов пока нет</div>
          </Card>
        ) : (
          <div className="datasets-list">
            {datasets.map((dataset) => (
              <Card key={dataset.id} className="dataset-card">
                <div className="dataset-header">
                  <div className="dataset-name">{dataset.name}</div>
                  <div className="dataset-id">ID: {dataset.id}</div>
                </div>
                <div className="dataset-info">
                  <div className="dataset-info-item">
                    <span className="dataset-info-label">S3 путь:</span>
                    <span className="dataset-s3-path">{dataset.s3_path}</span>
                  </div>
                  <div className="dataset-info-item">
                    <span className="dataset-info-label">Создан:</span>
                    <span>{formatDate(dataset.created_at)}</span>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

