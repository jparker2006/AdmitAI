'use client';

import React from 'react';
import { WizardLayout, FormStep } from '@/components/onboarding';
import { useRouter } from 'next/navigation';

/**
 * Step 2 of the Student Onboarding Wizard - Placeholder
 * This is a placeholder for the second step of the wizard
 */
export default function OnboardingStep2() {
  const router = useRouter();

  const handleNext = () => {
    // Navigate to step 3 when implemented
    router.push('/onboarding/step-3');
  };

  const handleBack = () => {
    router.push('/onboarding/step-1');
  };

  return (
    <WizardLayout>
      <FormStep
        title="Academic Details"
        subtitle="Tell us about your academic background"
        onNext={handleNext}
        onBack={handleBack}
        showBackButton={true}
        isNextDisabled={false}
      >
        <div className="space-y-6">
          <div className="text-center py-12">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Step 2 - Academic Details
            </h3>
            <p className="text-gray-600">
              This step will collect information about your academic background,
              including GPA, test scores, coursework, and academic achievements.
            </p>
            <p className="text-sm text-gray-500 mt-4">
              This is a placeholder page. The actual form will be implemented next.
            </p>
          </div>
        </div>
      </FormStep>
    </WizardLayout>
  );
} 