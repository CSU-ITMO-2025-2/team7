import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { runsService, datasetsService, authService } from '../../services/api';
import { Input } from '../../components/Input/Input';
import { Button } from '../../components/Button/Button';
import { Alert } from '../../components/Alert/Alert';
import { Card } from '../../components/Card/Card';
import './Home.css';

export const Home = () => {
  const navigate = useNavigate();
  const [runs, setRuns] = useState([]);
  const [datasets, setDatasets] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingRuns, setIsLoadingRuns] = useState(true);
  const [isLoadingDatasets, setIsLoadingDatasets] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [datasetId, setDatasetId] = useState('');
  const [configuration, setConfiguration] = useState('{}');
  const [userId, setUserId] = useState(null);

  useEffect(() => {
    loadUserAndData();
  }, []);

  const loadUserAndData = async () => {
    try {
      const user = await authService.getCurrentUser();
      setUserId(user.id);
      await Promise.all([loadRuns(), loadDatasets(user.id)]);
    } catch (err) {
      setError('Не удалось загрузить данные: ' + err.message);
      setIsLoadingRuns(false);
      setIsLoadingDatasets(false);
    }
  };

  const loadRuns = async () => {
    setIsLoadingRuns(true);
    try {
      const data = await runsService.getRuns();
      setRuns(data);
    } catch (err) {
      setError('Не удалось загрузить список запусков: ' + err.message);
    } finally {
      setIsLoadingRuns(false);
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!datasetId) {
      setError('Выберите датасет');
      return;
    }

    let config = {};
    if (configuration.trim()) {
      try {
        config = JSON.parse(configuration);
      } catch (err) {
        setError('Configuration должен быть валидным JSON');
        return;
      }
    }

    setIsLoading(true);
    try {
      const run = await runsService.createRun(Number(datasetId), config);
      setSuccess(`Запуск #${run.id} создан со статусом "${run.status}"`);
      setDatasetId('');
      setConfiguration('{}');
      await loadRuns();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return '#28a745';
      case 'failed':
        return '#dc3545';
      case 'processing':
        return '#ffc107';
      case 'in queue':
        return '#17a2b8';
      default:
        return '#6c757d';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('ru-RU');
  };

  return (
    <div className="home">
      <section className="home-section">
        <h2 className="section-title">Создать запуск</h2>
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
          {isLoadingDatasets ? (
            <div className="loading">Загрузка датасетов...</div>
          ) : datasets.length === 0 ? (
            <div className="no-datasets-message">
              <p>У вас пока нет датасетов. Сначала загрузите датасет.</p>
              <Button onClick={() => navigate('/datasets')}>
                Перейти к загрузке датасетов
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="input-group">
                <label className="input-label">Выберите датасет</label>
                <select
                  className="input select-input"
                  value={datasetId}
                  onChange={(e) => setDatasetId(e.target.value)}
                  required
                >
                  <option value="">-- Выберите датасет --</option>
                  {datasets.map((dataset) => (
                    <option key={dataset.id} value={dataset.id}>
                      {dataset.name} (ID: {dataset.id})
                    </option>
                  ))}
                </select>
              </div>
              <div className="input-group">
                <label className="input-label">Configuration (JSON)</label>
                <textarea
                  className="input"
                  value={configuration}
                  onChange={(e) => setConfiguration(e.target.value)}
                  placeholder='{"param": "value"}'
                />
              </div>
              <div className="form-actions">
                <Button type="submit" disabled={isLoading}>
                  {isLoading ? 'Создание...' : 'Создать запуск'}
                </Button>
                <Button type="button" variant="secondary" onClick={loadRuns} disabled={isLoadingRuns}>
                  Обновить список
                </Button>
              </div>
            </form>
          )}
        </Card>
      </section>

      <section className="home-section">
        <h2 className="section-title">Мои запуски</h2>
        {isLoadingRuns ? (
          <Card>
            <div className="loading">Загрузка...</div>
          </Card>
        ) : runs.length === 0 ? (
          <Card>
            <div className="empty-state">Запусков пока нет</div>
          </Card>
        ) : (
          <div className="runs-list">
            {runs.map((run) => (
              <Card key={run.id} className="run-card">
                <div className="run-header">
                  <div className="run-id">Запуск #{run.id}</div>
                  <div
                    className="run-status"
                    style={{ backgroundColor: getStatusColor(run.status) }}
                  >
                    {run.status}
                  </div>
                </div>
                <div className="run-info">
                  <div className="run-info-item">
                    <span className="run-info-label">Датасет ID:</span>
                    <span>{run.dataset_id}</span>
                  </div>
                  <div className="run-info-item">
                    <span className="run-info-label">Создан:</span>
                    <span>{formatDate(run.created_at)}</span>
                  </div>
                  {Object.keys(run.configuration || {}).length > 0 && (
                    <div className="run-info-item">
                      <span className="run-info-label">Configuration:</span>
                      <pre className="run-config">
                        {JSON.stringify(run.configuration, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

