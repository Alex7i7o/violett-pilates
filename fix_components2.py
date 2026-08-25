import sys

input_field = """import React from 'react';

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
"""

select_field = """import React from 'react';

interface SelectFieldProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: { value: string; label: string }[];
  error?: string;
}

export const SelectField: React.FC<SelectFieldProps> = ({ 
  label, 
  options, 
  error, 
  className = '', 
  ...props 
}) => {
  return (
    <div className="w-full">
      {label && <label className="block text-sm font-semibold mb-1 text-foreground">{label}</label>}
      <select
        className={`w-full p-2.5 rounded-xl border ${error ? 'border-red-500' : 'border-violett-200'} focus:outline-none focus:ring-2 focus:ring-violett-500 bg-white ${className}`}
        {...props}
      >
        <option value="">Seleccionar...</option>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <p className="text-red-500 text-xs mt-1 font-medium">{error}</p>}
    </div>
  );
};
"""

with open('frontend/src/components/ui/InputField.tsx', 'w', encoding='utf-8') as f:
    f.write(input_field)

with open('frontend/src/components/ui/SelectField.tsx', 'w', encoding='utf-8') as f:
    f.write(select_field)

print("Done generating components correctly")
