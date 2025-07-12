'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { WizardLayout, FormStep, TextInput } from '@/components/onboarding';
import { useOnboarding } from '@/context/onboarding-context';
import { ValidationErrors } from '@/types/onboarding';

/**
 * Step 1 of the Student Onboarding Wizard
 * Collects basic student information: name, email, graduation year, high school, CEEB code
 * Includes FERPA/COPPA consent checkbox
 */
export default function OnboardingStep1() {
  const router = useRouter();
  const { 
    studentData, 
    updateStudentData, 
    validationErrors, 
    setValidationErrors 
  } = useOnboarding();
  
  const [localErrors, setLocalErrors] = useState<ValidationErrors>({});

  /**
   * Validates the form data before proceeding to next step
   */
  const validateForm = (): boolean => {
    const errors: ValidationErrors = {};
    
    if (!studentData.firstName.trim()) {
      errors.firstName = 'First name is required';
    }
    
    if (!studentData.lastName.trim()) {
      errors.lastName = 'Last name is required';
    }
    
    if (!studentData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(studentData.email)) {
      errors.email = 'Please enter a valid email address';
    }
    
    if (!studentData.graduationYear) {
      errors.graduationYear = 'Graduation year is required';
    } else {
      const currentYear = new Date().getFullYear();
      const year = studentData.graduationYear;
      if (year < currentYear || year > currentYear + 10) {
        errors.graduationYear = 'Please enter a valid graduation year';
      }
    }
    
    if (!studentData.highSchoolName.trim()) {
      errors.highSchoolName = 'High school name is required';
    }
    
    if (!studentData.ceebCode.trim()) {
      errors.ceebCode = 'CEEB code is required';
    } else if (!/^\d{6}$/.test(studentData.ceebCode)) {
      errors.ceebCode = 'CEEB code must be exactly 6 digits';
    }
    
    if (!studentData.ferpaConsent) {
      errors.ferpaConsent = 'You must agree to FERPA/COPPA consent to continue';
    }
    
    setLocalErrors(errors);
    setValidationErrors(errors);
    
    return Object.keys(errors).length === 0;
  };

  /**
   * Handles proceeding to the next step
   */
  const handleNext = () => {
    if (validateForm()) {
      router.push('/onboarding/step-2');
    }
  };

  /**
   * Handles going back to previous step (not applicable for step 1)
   */
  const handleBack = () => {
    // Could navigate to a landing page or dashboard
    router.push('/');
  };

  return (
    <WizardLayout>
      <FormStep
        title="Basic Information"
        subtitle="Tell us about yourself to get started"
        onNext={handleNext}
        onBack={handleBack}
        showBackButton={false}
        isNextDisabled={false}
      >
        <div className="space-y-6">
          {/* Name Fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <TextInput
              label="First Name"
              name="firstName"
              value={studentData.firstName}
              onChange={(value) => updateStudentData({ firstName: value })}
              placeholder="Enter your first name"
              required
              error={localErrors.firstName}
            />
            
            <TextInput
              label="Last Name"
              name="lastName"
              value={studentData.lastName}
              onChange={(value) => updateStudentData({ lastName: value })}
              placeholder="Enter your last name"
              required
              error={localErrors.lastName}
            />
          </div>

          {/* Email */}
          <TextInput
            label="Email Address"
            name="email"
            type="email"
            value={studentData.email}
            onChange={(value) => updateStudentData({ email: value })}
            placeholder="Enter your email address"
            required
            error={localErrors.email}
            helperText="We'll use this to send you important updates about your application"
          />

          {/* Graduation Year */}
          <TextInput
            label="Graduation Year"
            name="graduationYear"
            type="number"
            value={studentData.graduationYear?.toString() || ''}
            onChange={(value) => updateStudentData({ 
              graduationYear: value ? parseInt(value) : null 
            })}
            placeholder="e.g., 2025"
            required
            error={localErrors.graduationYear}
            helperText="The year you plan to graduate from high school"
          />

          {/* High School Information */}
          <div className="space-y-4">
            <TextInput
              label="High School Name"
              name="highSchoolName"
              value={studentData.highSchoolName}
              onChange={(value) => updateStudentData({ highSchoolName: value })}
              placeholder="Enter your high school name"
              required
              error={localErrors.highSchoolName}
            />

            <TextInput
              label="CEEB Code"
              name="ceebCode"
              value={studentData.ceebCode}
              onChange={(value) => updateStudentData({ ceebCode: value })}
              placeholder="Enter 6-digit CEEB code"
              required
              error={localErrors.ceebCode}
              helperText="Your school's College Entrance Examination Board code (6 digits)"
            />
          </div>

          {/* FERPA/COPPA Consent */}
          <div className="space-y-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-start space-x-3">
              <Checkbox
                id="ferpaConsent"
                checked={studentData.ferpaConsent}
                onCheckedChange={(checked) => 
                  updateStudentData({ ferpaConsent: checked === true })
                }
                className="mt-1"
              />
              <div className="space-y-1">
                <Label 
                  htmlFor="ferpaConsent" 
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  FERPA/COPPA Consent Agreement
                  <span className="text-red-500 ml-1">*</span>
                </Label>
                <p className="text-sm text-gray-600">
                  I consent to the collection, use, and disclosure of my educational records 
                  in accordance with FERPA and COPPA regulations. I understand that this 
                  information will be used to provide college admissions guidance and services.
                </p>
                {localErrors.ferpaConsent && (
                  <p className="text-sm text-red-600">
                    {localErrors.ferpaConsent}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      </FormStep>
    </WizardLayout>
  );
} 