import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Input } from '../../components/Input/Input';
import { Button } from '../../components/Button/Button';
import { Alert } from '../../components/Alert/Alert';
import { Card } from '../../components/Card/Card';
import './Register.css';

export const Register = () => {
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsLoading(true);

    const result = await register(login, password);

    if (result.success) {
      setSuccess('Пользователь успешно создан! Теперь войдите.');
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } else {
      setError(result.error);
    }

    setIsLoading(false);
  };

  return (
    <div className="auth-page">
      <Card className="auth-card">
        <h2 className="auth-title">Регистрация</h2>
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
            minLength={6}
            autoComplete="new-password"
            error={password && password.length < 6 ? 'Минимум 6 символов' : ''}
          />
          <Button type="submit" disabled={isLoading} className="auth-submit">
            {isLoading ? 'Регистрация...' : 'Зарегистрироваться'}
          </Button>
        </form>
        <div className="auth-footer">
          <p>
            Уже есть аккаунт? <a href="/login">Войти</a>
          </p>
        </div>
      </Card>
    </div>
  );
};

