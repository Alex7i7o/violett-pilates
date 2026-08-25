skeleton_code = '''import React from 'react';
import { cn } from '../../lib/utils';

export function Skeleton({ className = '' }: { className?: string }) {
  return (
    <div 
      className={cn(
        "relative overflow-hidden bg-violett-100 rounded-md", 
        className
      )} 
    >
      <div className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/60 to-transparent" />
    </div>
  );
}
'''
with open('frontend/src/components/ui/Skeleton.tsx', 'w', encoding='utf-8') as f:
    f.write(skeleton_code)
print('Skeleton updated')
