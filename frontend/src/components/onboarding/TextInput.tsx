import React from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { TextInputProps } from '@/types/onboarding';

/**
 * TextInput component with label, validation, and error display
 * Supports different input types and shows helper text
 */
export function TextInput({
  label,
  name,
  value,
  onChange,
  placeholder,
  required = false,
  error,
  type = 'text',
  helperText,
}: TextInputProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor={name} className="text-sm font-medium">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </Label>
      
      <Input
        id={name}
        name={name}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={`${
          error ? 'border-red-500 focus:border-red-500' : ''
        }`}
        aria-describedby={error ? `${name}-error` : helperText ? `${name}-helper` : undefined}
      />
      
      {error && (
        <div id={`${name}-error`} className="text-sm text-red-600">
          {error}
        </div>
      )}
      
      {helperText && !error && (
        <div id={`${name}-helper`} className="text-sm text-gray-500">
          {helperText}
        </div>
      )}
    </div>
  );
} 