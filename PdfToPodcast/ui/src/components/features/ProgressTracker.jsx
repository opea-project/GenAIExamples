import { Loader2, CheckCircle } from 'lucide-react';
import { Card, CardBody, Progress } from '@components/ui';
import { cn } from '@utils/helpers';

const steps = [
  { id: 1, label: 'Uploading PDF', threshold: 10 },
  { id: 2, label: 'Extracting content', threshold: 30 },
  { id: 3, label: 'Analyzing structure', threshold: 50 },
  { id: 4, label: 'Generating dialogue', threshold: 70 },
  { id: 5, label: 'Finalizing script', threshold: 90 },
];

export const ProgressTracker = ({ progress = 0, message = 'Processing...' }) => {
  return (
    <Card>
      <CardBody>
        <div className="text-center space-y-6">
          {/* Animated Icon */}
          <div className="relative">
            <Loader2 className="w-16 h-16 text-primary-500 mx-auto animate-spin" />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-12 h-12 bg-primary-100 rounded-full animate-pulse" />
            </div>
          </div>

          {/* Message */}
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              {message}
            </h2>
            <p className="text-gray-600">
              This may take a few minutes. Please don't close this page.
            </p>
          </div>

          {/* Progress Bar */}
          <div className="max-w-md mx-auto">
            <Progress value={progress} size="lg" showLabel />
          </div>

          {/* Step List */}
          <div className="max-w-md mx-auto space-y-2 text-left">
            {steps.map((step) => {
              const isCompleted = progress >= step.threshold;
              const isCurrent =
                progress >= (steps[step.id - 2]?.threshold || 0) &&
                progress < step.threshold;

              return (
                <div
                  key={step.id}
                  className={cn(
                    'flex items-center gap-3 p-3 rounded-lg transition-all',
                    isCompleted && 'bg-success-50',
                    isCurrent && 'bg-primary-50',
                    !isCompleted && !isCurrent && 'bg-gray-50'
                  )}
                >
                  <div
                    className={cn(
                      'w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0',
                      isCompleted &&
                        'bg-success-500 text-white',
                      isCurrent &&
                        'bg-primary-500 text-white animate-pulse',
                      !isCompleted &&
                        !isCurrent &&
                        'bg-gray-300 text-gray-500'
                    )}
                  >
                    {isCompleted ? (
                      <CheckCircle className="w-4 h-4" />
                    ) : (
                      <span className="text-xs font-bold">{step.id}</span>
                    )}
                  </div>
                  <span
                    className={cn(
                      'text-sm font-medium',
                      isCompleted && 'text-success-700',
                      isCurrent && 'text-primary-700',
                      !isCompleted && !isCurrent && 'text-gray-500'
                    )}
                  >
                    {step.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </CardBody>
    </Card>
  );
};

export default ProgressTracker;
