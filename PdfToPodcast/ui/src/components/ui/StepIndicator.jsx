import { Check } from 'lucide-react';
import { cn } from '@utils/helpers';

export const StepIndicator = ({ steps, currentStep }) => {
  return (
    <div className="w-full py-8">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const stepNumber = index + 1;
          const isCompleted = stepNumber < currentStep;
          const isCurrent = stepNumber === currentStep;

          return (
            <div key={step.id} className="flex items-center flex-1">
              {/* Step circle */}
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    'w-12 h-12 rounded-full flex items-center justify-center font-semibold transition-all',
                    isCompleted &&
                      'bg-success-500 text-white',
                    isCurrent &&
                      'bg-primary-600 text-white ring-4 ring-primary-100',
                    !isCompleted &&
                      !isCurrent &&
                      'bg-gray-200 text-gray-600'
                  )}
                >
                  {isCompleted ? (
                    <Check className="w-6 h-6" />
                  ) : (
                    stepNumber
                  )}
                </div>
                <div className="mt-2 text-center">
                  <p
                    className={cn(
                      'text-sm font-medium',
                      isCurrent ? 'text-primary-600' : 'text-gray-600'
                    )}
                  >
                    {step.title}
                  </p>
                  {step.subtitle && (
                    <p className="text-xs text-gray-500 mt-1">
                      {step.subtitle}
                    </p>
                  )}
                </div>
              </div>

              {/* Connector line */}
              {index < steps.length - 1 && (
                <div
                  className={cn(
                    'flex-1 h-1 mx-4 rounded transition-all',
                    isCompleted ? 'bg-success-500' : 'bg-gray-200'
                  )}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default StepIndicator;
