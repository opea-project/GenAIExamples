import { AlertCircle, CheckCircle, Info, XCircle, X } from 'lucide-react';
import { cn } from '@utils/helpers';

const variants = {
  info: {
    bg: 'bg-blue-50 border-blue-200',
    icon: 'text-blue-600',
    text: 'text-blue-800',
    Icon: Info,
  },
  success: {
    bg: 'bg-success-50 border-success-200',
    icon: 'text-success-600',
    text: 'text-success-800',
    Icon: CheckCircle,
  },
  warning: {
    bg: 'bg-warning-50 border-warning-200',
    icon: 'text-warning-600',
    text: 'text-warning-800',
    Icon: AlertCircle,
  },
  error: {
    bg: 'bg-error-50 border-error-200',
    icon: 'text-error-600',
    text: 'text-error-800',
    Icon: XCircle,
  },
};

export const Alert = ({
  variant = 'info',
  title,
  message,
  onClose,
  className = '',
}) => {
  const config = variants[variant];
  const Icon = config.Icon;

  return (
    <div
      className={cn(
        'p-4 rounded-lg border flex items-start gap-3',
        config.bg,
        className
      )}
    >
      <Icon className={cn('w-5 h-5 flex-shrink-0 mt-0.5', config.icon)} />
      <div className="flex-1">
        {title && (
          <h4 className={cn('font-medium mb-1', config.text)}>{title}</h4>
        )}
        {message && <p className={cn('text-sm', config.text)}>{message}</p>}
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className={cn('flex-shrink-0 hover:opacity-70', config.icon)}
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};

export default Alert;
