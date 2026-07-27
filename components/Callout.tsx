import { AlertCircle, Info, CheckCircle, AlertTriangle } from 'lucide-react';
import { ReactNode } from 'react';

type CalloutType = 'info' | 'warning' | 'error' | 'success';

interface CalloutProps {
  type: CalloutType;
  title?: string;
  children: ReactNode;
}

const icons: Record<CalloutType, typeof AlertCircle> = {
  info: Info,
  warning: AlertTriangle,
  error: AlertCircle,
  success: CheckCircle,
};

const styles: Record<
  CalloutType,
  {
    bg: string;
    border: string;
    icon: string;
    title: string;
  }
> = {
  info: {
    bg: 'bg-blue-50 dark:bg-blue-950/20',
    border: 'border-blue-200 dark:border-blue-900',
    icon: 'text-blue-600 dark:text-blue-400',
    title: 'text-blue-900 dark:text-blue-100',
  },
  warning: {
    bg: 'bg-yellow-50 dark:bg-yellow-950/20',
    border: 'border-yellow-200 dark:border-yellow-900',
    icon: 'text-yellow-600 dark:text-yellow-400',
    title: 'text-yellow-900 dark:text-yellow-100',
  },
  error: {
    bg: 'bg-red-50 dark:bg-red-950/20',
    border: 'border-red-200 dark:border-red-900',
    icon: 'text-red-600 dark:text-red-400',
    title: 'text-red-900 dark:text-red-100',
  },
  success: {
    bg: 'bg-green-50 dark:bg-green-950/20',
    border: 'border-green-200 dark:border-green-900',
    icon: 'text-green-600 dark:text-green-400',
    title: 'text-green-900 dark:text-green-100',
  },
};

export function Callout({ type, title, children }: CalloutProps) {
  const Icon = icons[type];
  const style = styles[type];

  return (
    <div className={`my-6 rounded-lg border ${style.bg} ${style.border} p-4`}>
      <div className="flex gap-3">
        <Icon className={`h-5 w-5 flex-shrink-0 mt-0.5 ${style.icon}`} />
        <div className="flex-1">
          {title && <p className={`font-semibold mb-1 ${style.title}`}>{title}</p>}
          <div className="text-sm prose-reset">{children}</div>
        </div>
      </div>
    </div>
  );
}
