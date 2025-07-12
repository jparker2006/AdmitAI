import React from 'react';
import { Progress } from '@/components/ui/progress';
import { ProgressBarProps } from '@/types/onboarding';

/**
 * ProgressBar component that displays the current step in the onboarding wizard
 * Shows visual progress with step numbers and optional labels
 */
export function ProgressBar({ 
  currentStep, 
  totalSteps, 
  stepLabels = [] 
}: ProgressBarProps) {
  const progressPercentage = (currentStep / totalSteps) * 100;

  return (
    <div className="w-full max-w-2xl mx-auto mb-8">
      <div className="flex justify-between items-center mb-4">
        <div className="text-sm font-medium text-gray-700">
          Step {currentStep} of {totalSteps}
        </div>
        <div className="text-sm text-gray-500">
          {Math.round(progressPercentage)}% Complete
        </div>
      </div>
      
      <Progress value={progressPercentage} className="h-2" />
      
      {stepLabels.length > 0 && (
        <div className="flex justify-between mt-4 text-xs text-gray-500">
          {stepLabels.map((label, index) => (
            <div
              key={index}
              className={`${
                index + 1 <= currentStep 
                  ? 'text-blue-600 font-medium' 
                  : 'text-gray-400'
              }`}
            >
              {label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
} 