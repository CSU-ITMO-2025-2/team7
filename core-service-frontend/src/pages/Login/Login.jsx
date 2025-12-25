import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Input } from '../../components/Input/Input';
import { Button } from '../../components/Button/Button';
import { Alert } from '../../components/Alert/Alert';
import { Card } from '../../components/Card/Card';
import './Login.css';

export const Login = () => {
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login: loginUser } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    const result = await loginUser(login, password);

    if (result.success) {
      navigate('/');
    } else {
      setError(result.error);
    }

    setIsLoading(false);
  };

  return (
    <div className="auth-page">
      <Card className="auth-card">
        <h2 className="auth-title">Вход</h2>
        {error && (
          <Alert variant="error" onClose={() => setError('')}>
            {error}
          </Alert>
        )}
        <form onSubmit={handleSubmit}>
          <Input
            label="Логин"
            type="text"
            value={login}
            onChange={(e) => setLogin(e.target.value)}
            required
            autoComplete="username"
          />
          <Input
            label="Пароль"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
          <Button type="submit" disabled={isLoading} className="auth-submit">
            {isLoading ? 'Вход...' : 'Войти'}
          </Button>
        </form>
        <div className="auth-footer">
          <p>
            Нет аккаунта? <a href="/register">Зарегистрироваться</a>
          </p>
        </div>
      </Card>
    </div>
  );
};

