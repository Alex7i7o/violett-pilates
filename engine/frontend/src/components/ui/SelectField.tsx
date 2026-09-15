import React from 'react';

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
        className={`w-full p-2.5 rounded-xl border ${error ? 'border-red-500' : 'border-primary-light'} focus:outline-none focus:ring-2 focus:ring-primary-main bg-white ${className}`}
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
