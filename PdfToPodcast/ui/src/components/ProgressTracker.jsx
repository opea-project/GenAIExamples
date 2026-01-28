import { Loader2, CheckCircle2 } from 'lucide-react';

const ProgressTracker = ({ progress, message }) => {
  // Determine steps based on message content
  const getSteps = () => {
    const msg = message.toLowerCase();

    if (msg.includes('audio') || msg.includes('generating podcast') || msg.includes('creating podcast')) {
      // Audio generation phase
      return [
        { label: 'Processing script', threshold: 20 },
        { label: 'Generating host audio', threshold: 40 },
        { label: 'Generating guest audio', threshold: 60 },
        { label: 'Combining audio segments', threshold: 80 },
        { label: 'Finalizing podcast', threshold: 95 }
      ];
    } else {
      // Script generation phase
      return [
        { label: 'Analyzing PDF content', threshold: 20 },
        { label: 'Extracting key concepts', threshold: 40 },
        { label: 'Creating dialogue flow', threshold: 60 },
        { label: 'Generating conversation', threshold: 80 },
        { label: 'Finalizing script', threshold: 95 }
      ];
    }
  };

  const steps = getSteps();

  return (
    <div className="card">
      <div className="text-center">
        <Loader2 className="w-16 h-16 text-primary-500 mx-auto mb-6 animate-spin" />

        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          {message || 'Processing...'}
        </h2>

        <div className="w-full bg-gray-200 rounded-full h-4 mb-4">
          <div
            className="bg-primary-600 h-4 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>

        <p className="text-lg font-medium text-gray-600">
          {progress}% Complete
        </p>

        <div className="mt-8 space-y-3 text-left max-w-md mx-auto">
          {steps.map((step, index) => {
            const isCompleted = progress >= step.threshold;
            const isActive = progress >= (index > 0 ? steps[index - 1].threshold : 0) && progress < step.threshold;

            return (
              <div
                key={index}
                className={`flex items-center transition-colors ${
                  isCompleted ? 'text-green-600' :
                  isActive ? 'text-primary-600 font-medium' :
                  'text-gray-400'
                }`}
              >
                {isCompleted ? (
                  <CheckCircle2 className="w-4 h-4 mr-3 flex-shrink-0" />
                ) : (
                  <div className={`w-2 h-2 rounded-full mr-3 flex-shrink-0 ${
                    isCompleted ? 'bg-green-600' :
                    isActive ? 'bg-primary-600 animate-pulse' :
                    'bg-gray-400'
                  }`} />
                )}
                <span>{step.label}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default ProgressTracker;
