import React from 'react';
import { ProgressBar } from './ProgressBar';
import { Button } from '@/components/ui/button';
import { useOnboarding } from '@/context/onboarding-context';

interface WizardLayoutProps {
  children: React.ReactNode;
  stepLabels?: string[];
}

/**
 * WizardLayout component that provides the overall layout structure for the onboarding wizard
 * Includes progress bar, save & resume functionality, and consistent page layout
 */
export function WizardLayout({ children, stepLabels }: WizardLayoutProps) {
  const { currentStep, saveAndResume, isLoading } = useOnboarding();
  
  const totalSteps = 4;
  const defaultStepLabels = [
    'Basic Information',
    'Academic Details',
    'Extracurriculars',
    'College Preferences'
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto py-8 px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Student Onboarding
          </h1>
          <p className="text-gray-600">
            Complete your profile to get started with college admissions
          </p>
        </div>

        {/* Progress Bar */}
        <ProgressBar 
          currentStep={currentStep} 
          totalSteps={totalSteps}
          stepLabels={stepLabels || defaultStepLabels}
        />

        {/* Main Content */}
        <div className="flex justify-center">
          {children}
        </div>

        {/* Save & Resume Button */}
        <div className="flex justify-center mt-8">
          <Button
            variant="outline"
            onClick={saveAndResume}
            disabled={isLoading}
            className="px-6"
          >
            {isLoading ? 'Saving...' : 'Save & Resume Later'}
          </Button>
        </div>
      </div>
    </div>
  );
} 