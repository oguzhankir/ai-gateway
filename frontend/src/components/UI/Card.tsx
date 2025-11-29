/** Reusable Card component */

import { cn } from '@/lib/utils';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'outlined';
  title?: string;
}

export function Card({ children, className, variant = 'default', title }: CardProps) {
  return (
    <div
      className={cn(
        'rounded-lg p-6',
        variant === 'outlined'
          ? 'border border-gray-200 bg-white'
          : 'bg-white shadow',
        className
      )}
    >
      {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}
      {children}
    </div>
  );
}
