'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { StudentData, ValidationErrors, OnboardingContextType } from '@/types/onboarding';

const initialStudentData: StudentData = {
  firstName: '',
  lastName: '',
  email: '',
  graduationYear: null,
  highSchoolName: '',
  ceebCode: '',
  ferpaConsent: false,
};

const OnboardingContext = createContext<OnboardingContextType | undefined>(undefined);

interface OnboardingProviderProps {
  children: ReactNode;
}

/**
 * OnboardingProvider component that manages the student onboarding state
 * Provides Save & Resume functionality through React Context
 */
export function OnboardingProvider({ children }: OnboardingProviderProps) {
  const [studentData, setStudentData] = useState<StudentData>(initialStudentData);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  /**
   * Updates student data with partial data
   */
  const updateStudentData = useCallback((data: Partial<StudentData>) => {
    setStudentData(prev => ({ ...prev, ...data }));
  }, []);

  /**
   * Save & Resume functionality placeholder
   * In a real app, this would save to backend/localStorage
   */
  const saveAndResume = useCallback(() => {
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      console.log('Saving student data:', studentData);
      // In production, this would save to backend
      localStorage.setItem('studentOnboardingData', JSON.stringify(studentData));
      setIsLoading(false);
    }, 1000);
  }, [studentData]);

  const value: OnboardingContextType = {
    studentData,
    updateStudentData,
    validationErrors,
    setValidationErrors,
    currentStep,
    setCurrentStep,
    saveAndResume,
    isLoading,
  };

  return (
    <OnboardingContext.Provider value={value}>
      {children}
    </OnboardingContext.Provider>
  );
}

/**
 * Custom hook to use the onboarding context
 */
export function useOnboarding() {
  const context = useContext(OnboardingContext);
  if (context === undefined) {
    throw new Error('useOnboarding must be used within an OnboardingProvider');
  }
  return context;
} 