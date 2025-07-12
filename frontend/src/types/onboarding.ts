/**
 * TypeScript interfaces for the Student Onboarding & Profile Wizard
 */

export interface StudentData {
  // Step 1 - Basic Information
  firstName: string;
  lastName: string;
  email: string;
  graduationYear: number | null;
  highSchoolName: string;
  ceebCode: string;
  ferpaConsent: boolean;
  
  // Future steps (placeholders)
  // Step 2 - Academic Information
  // Step 3 - Extracurriculars
  // Step 4 - College Preferences
}

export interface ValidationErrors {
  firstName?: string;
  lastName?: string;
  email?: string;
  graduationYear?: string;
  highSchoolName?: string;
  ceebCode?: string;
  ferpaConsent?: string;
}

export interface OnboardingContextType {
  studentData: StudentData;
  updateStudentData: (data: Partial<StudentData>) => void;
  validationErrors: ValidationErrors;
  setValidationErrors: (errors: ValidationErrors) => void;
  currentStep: number;
  setCurrentStep: (step: number) => void;
  saveAndResume: () => void;
  isLoading: boolean;
}

export interface FormStepProps {
  children: any;
  title: string;
  subtitle?: string;
  onNext?: () => void;
  onBack?: () => void;
  isNextDisabled?: boolean;
  isBackDisabled?: boolean;
  showBackButton?: boolean;
}

export interface TextInputProps {
  label: string;
  name: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  required?: boolean;
  error?: string;
  type?: 'text' | 'email' | 'number';
  helperText?: string;
}

export interface ProgressBarProps {
  currentStep: number;
  totalSteps: number;
  stepLabels?: string[];
} 