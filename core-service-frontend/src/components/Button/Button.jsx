import './Button.css';

export const Button = ({ children, variant = 'primary', type = 'button', onClick, disabled, ...props }) => {
  return (
    <button
      type={type}
      className={`btn btn-${variant}`}
      onClick={onClick}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};

