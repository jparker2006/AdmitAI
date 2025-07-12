import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FormStepProps } from '@/types/onboarding';

/**
 * FormStep component that wraps form content with title, navigation buttons
 * Provides consistent layout and navigation for wizard steps
 */
export function FormStep({
  children,
  title,
  subtitle,
  onNext,
  onBack,
  isNextDisabled = false,
  isBackDisabled = false,
  showBackButton = true,
}: FormStepProps) {
  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="text-2xl font-bold text-center">{title}</CardTitle>
        {subtitle && (
          <CardDescription className="text-center text-gray-600">
            {subtitle}
          </CardDescription>
        )}
      </CardHeader>
      
      <CardContent className="space-y-6">
        {children}
        
        <div className="flex justify-between pt-6">
          {showBackButton ? (
            <Button
              type="button"
              variant="outline"
              onClick={onBack}
              disabled={isBackDisabled}
              className="px-6"
            >
              Back
            </Button>
          ) : (
            <div />
          )}
          
          <Button
            type="button"
            onClick={onNext}
            disabled={isNextDisabled}
            className="px-6"
          >
            Next
          </Button>
        </div>
      </CardContent>
    </Card>
  );
} 