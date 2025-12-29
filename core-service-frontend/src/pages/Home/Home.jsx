import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { runsService, datasetsService, trainService, artifactsService } from '../../services/api';
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
  const [modelOptions, setModelOptions] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [paramValues, setParamValues] = useState({});
  const [isLoadingModels, setIsLoadingModels] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const buildDefaultValues = (model) => {
    if (!model) {
      return {};
    }
    return model.parameters.reduce((acc, param) => {
      const value = param.default === null || param.default === undefined ? '' : String(param.default);
      return { ...acc, [param.name]: value };
    }, {});
  };

  const buildHyperparameters = () => ({ ...paramValues });

  const loadData = async () => {
    await Promise.all([loadRuns(), loadDatasets(), loadModelOptions()]);
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

  const loadDatasets = async () => {
    setIsLoadingDatasets(true);
    try {
      const data = await datasetsService.getDatasets();
      setDatasets(data);
    } catch (err) {
      setError('Не удалось загрузить список датасетов: ' + err.message);
    } finally {
      setIsLoadingDatasets(false);
    }
  };

  const loadModelOptions = async () => {
    setIsLoadingModels(true);
    try {
      const data = await trainService.getModels();
      const models = data.models || [];
      setModelOptions(models);
      if (models.length > 0) {
        const nextModel = models.find((model) => model.name === selectedModel)?.name
          || models[0].name;
        setSelectedModel(nextModel);
        const modelSpec = models.find((model) => model.name === nextModel);
        setParamValues(buildDefaultValues(modelSpec));
      } else {
        setSelectedModel('');
        setParamValues({});
      }
    } catch (err) {
      setError('Не удалось загрузить список моделей: ' + err.message);
    } finally {
      setIsLoadingModels(false);
    }
  };

  const handleModelChange = (event) => {
    const nextModel = event.target.value;
    setSelectedModel(nextModel);
    const modelSpec = modelOptions.find((model) => model.name === nextModel);
    setParamValues(buildDefaultValues(modelSpec));
  };

  const handleParamChange = (name, value) => {
    setParamValues((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!datasetId) {
      setError('Выберите датасет');
      return;
    }

    if (!selectedModel) {
      setError('Выберите модель');
      return;
    }

    const modelSpec = modelOptions.find((model) => model.name === selectedModel);
    if (!modelSpec) {
      setError('Выберите модель');
      return;
    }

    const config = {
      model: selectedModel,
      hyperparameters: buildHyperparameters(),
    };

    setIsLoading(true);
    try {
      const run = await runsService.createRun(Number(datasetId), config);
      setSuccess(`Запуск #${run.id} создан со статусом "${run.status}"`);
      setDatasetId('');
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

  const downloadFile = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  const handleDownloadModel = async (runId) => {
    setError('');
    setSuccess('');
    try {
      const { blob, filename } = await artifactsService.downloadModel(runId);
      downloadFile(blob, filename);
    } catch (err) {
      if (err?.status === 404) {
        setError(`Модель для запуска #${runId} пока не доступна`);
      } else {
        setError(err?.message || 'Не удалось скачать модель');
      }
    }
  };

  const handleDownloadResults = async (runId) => {
    setError('');
    setSuccess('');
    try {
      const { blob, filename } = await artifactsService.downloadResults(runId);
      downloadFile(blob, filename);
    } catch (err) {
      if (err?.status === 404) {
        setError(`Результаты для запуска #${runId} пока не доступны`);
      } else {
        setError(err?.message || 'Не удалось скачать результаты');
      }
    }
  };

  const selectedModelSpec = modelOptions.find((model) => model.name === selectedModel);

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
              {isLoadingModels ? (
                <div className="loading">Загрузка моделей...</div>
              ) : modelOptions.length === 0 ? (
                <div className="empty-state">Нет доступных моделей</div>
              ) : (
                <>
                  <div className="input-group">
                    <label className="input-label">Модель</label>
                    <select
                      className="input select-input"
                      value={selectedModel}
                      onChange={handleModelChange}
                      required
                    >
                      {modelOptions.map((model) => (
                        <option key={model.name} value={model.name}>
                          {model.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  {selectedModelSpec && (
                    <div className="model-params">
                      {selectedModelSpec.parameters.map((param) => (
                        <div className="input-group" key={param.name}>
                          <label className="input-label">{param.name}</label>
                          {param.type === 'enum' || param.type === 'bool' ? (
                            <select
                              className="input select-input"
                              value={paramValues[param.name] ?? ''}
                              onChange={(e) => handleParamChange(param.name, e.target.value)}
                            >
                              {(param.options || []).map((option) => (
                                <option
                                  key={`${param.name}-${String(option)}`}
                                  value={String(option)}
                                >
                                  {String(option)}
                                </option>
                              ))}
                            </select>
                          ) : (
                            <input
                              className="input"
                              type="number"
                              value={paramValues[param.name] ?? ''}
                              onChange={(e) => handleParamChange(param.name, e.target.value)}
                            />
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
              <div className="form-actions">
                <Button
                  type="submit"
                  disabled={isLoading || isLoadingModels || modelOptions.length === 0}
                >
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
                {run.status === 'completed' && (
                  <div className="run-actions">
                    <Button onClick={() => handleDownloadModel(run.id)}>
                      Скачать модель
                    </Button>
                    <Button variant="secondary" onClick={() => handleDownloadResults(run.id)}>
                      Скачать результаты
                    </Button>
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
