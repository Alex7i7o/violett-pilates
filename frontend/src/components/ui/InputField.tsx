import React from 'react';

interface InputFieldProps extends React.InputHTMLAttributes<HTMLInputElement | HTMLTextAreaElement> {
  label?: string;
  error?: string;
  multiline?: boolean;
  rows?: number;
}

export const InputField: React.FC<InputFieldProps> = ({ 
  label, 
  error, 
  className = '', 
  multiline = false,
  rows = 3,
  ...props 
}) => {
  return (
    <div className="w-full">
      {label && <label className="block text-sm font-semibold mb-1 text-foreground">{label}</label>}
      {multiline ? (
        <textarea
          className={`w-full p-2.5 rounded-xl border ${error ? 'border-red-500' : 'border-violett-200'} focus:outline-none focus:ring-2 focus:ring-violett-500 bg-white ${className}`}
          rows={rows}
          {...(props as React.TextareaHTMLAttributes<HTMLTextAreaElement>)}
        />
      ) : (
        <input
          className={`w-full p-2.5 rounded-xl border ${error ? 'border-red-500' : 'border-violett-200'} focus:outline-none focus:ring-2 focus:ring-violett-500 bg-white ${className}`}
          {...(props as React.InputHTMLAttributes<HTMLInputElement>)}
        />
      )}
      {error && <p className="text-red-500 text-xs mt-1 font-medium">{error}</p>}
    </div>
  );
};
