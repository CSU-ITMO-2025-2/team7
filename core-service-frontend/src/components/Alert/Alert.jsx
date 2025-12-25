import './Alert.css';

export const Alert = ({ children, variant = 'info', onClose }) => {
  return (
    <div className={`alert alert-${variant}`}>
      <span>{children}</span>
      {onClose && (
        <button className="alert-close" onClick={onClose} aria-label="Закрыть">
          ×
        </button>
      )}
    </div>
  );
};

