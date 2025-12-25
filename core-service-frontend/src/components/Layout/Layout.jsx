import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../Button/Button';
import './Layout.css';

export const Layout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, logout } = useAuth();

  return (
    <div className="layout">
      <header className="header">
        <div className="header-content">
          <h1 className="header-title" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
            Core Service
          </h1>
          {isAuthenticated && (
            <nav className="header-nav">
              <Button
                variant={location.pathname === '/' ? 'primary' : 'secondary'}
                onClick={() => navigate('/')}
              >
                Запуски
              </Button>
              <Button
                variant={location.pathname === '/datasets' ? 'primary' : 'secondary'}
                onClick={() => navigate('/datasets')}
              >
                Датасеты
              </Button>
              <Button variant="secondary" onClick={logout}>
                Выйти
              </Button>
            </nav>
          )}
        </div>
      </header>
      <main className="main">{children}</main>
    </div>
  );
};

