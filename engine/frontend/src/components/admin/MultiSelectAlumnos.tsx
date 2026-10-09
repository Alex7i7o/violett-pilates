import React, { useState, useEffect, useRef } from 'react';
import { X, Check } from 'lucide-react';
import { getAdminAlumnos } from '../../lib/adminApi';

interface Alumno {
  id: string;
  nombre: string;
  apellido: string;
}

interface MultiSelectAlumnosProps {
  selectedIds: string[];
  onChange: (ids: string[]) => void;
}

export function MultiSelectAlumnos({ selectedIds = [], onChange }: MultiSelectAlumnosProps) {
  const [alumnos, setAlumnos] = useState<Alumno[]>([]);
  const [search, setSearch] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getAdminAlumnos().then(res => setAlumnos(res.data)).catch(console.error);
  }, []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredAlumnos = alumnos.filter(a => 
    `${a.nombre} ${a.apellido}`.toLowerCase().includes(search.toLowerCase())
  );

  const toggleAlumno = (id: string) => {
    if (selectedIds.includes(id)) {
      onChange(selectedIds.filter(x => x !== id));
    } else {
      onChange([...selectedIds, id]);
    }
  };

  const removeAlumno = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    onChange(selectedIds.filter(x => x !== id));
  };

  return (
    <div className="relative w-full" ref={wrapperRef}>
      <div 
        className="min-h-[42px] w-full p-2 rounded-xl border border-primary-light focus-within:ring-2 focus-within:ring-primary-main bg-white cursor-text flex flex-wrap gap-2 items-center"
        onClick={() => setIsOpen(true)}
      >
        {selectedIds.map(id => {
          const al = alumnos.find(a => a.id === id);
          if (!al) return null;
          return (
            <span key={id} className="bg-primary-light text-primary-main px-2 py-1 rounded-md text-xs font-semibold flex items-center gap-1">
              {al.nombre} {al.apellido}
              <X className="w-3 h-3 cursor-pointer hover:text-red-500" onClick={(e) => removeAlumno(e, id)} />
            </span>
          );
        })}
        <input 
          type="text" 
          placeholder={selectedIds.length === 0 ? "Buscar y seleccionar alumnos..." : ""}
          className="flex-1 outline-none min-w-[120px] text-sm bg-transparent"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
        />
      </div>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 max-h-60 overflow-y-auto bg-white border border-slate-200 rounded-xl shadow-lg">
          {filteredAlumnos.length > 0 ? filteredAlumnos.map(al => {
            const isSelected = selectedIds.includes(al.id);
            return (
              <div 
                key={al.id} 
                className={`p-2.5 px-4 text-sm cursor-pointer hover:bg-slate-50 flex items-center justify-between ${isSelected ? 'bg-slate-50 font-medium' : ''}`}
                onClick={() => {
                  toggleAlumno(al.id);
                  setSearch('');
                }}
              >
                <span>{al.nombre} {al.apellido}</span>
                {isSelected && <Check className="w-4 h-4 text-primary-main" />}
              </div>
            );
          }) : (
            <div className="p-3 text-sm text-slate-500 text-center">No se encontraron alumnos</div>
          )}
        </div>
      )}
    </div>
  );
}
