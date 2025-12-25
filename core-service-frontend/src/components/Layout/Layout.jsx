import { useAuth } from '../../context/AuthContext';
import { Button } from '../Button/Button';
import './Layout.css';

export const Layout = ({ children }) => {
  const { isAuthenticated, logout } = useAuth();

  return (
    <div className="layout">
      <header className="header">
        <div className="header-content">
          <h1 className="header-title">Core Service</h1>
          {isAuthenticated && (
            <nav className="header-nav">
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

