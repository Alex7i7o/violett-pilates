# -*- coding: utf-8 -*-
import re

with open('frontend/src/components/ui/Modal.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

target = """          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 15 }}
            animate={{ 
              opacity: 1, 
              scale: 1, 
              y: 0, 
              transition: { type: "spring", duration: 0.25, bounce: 0.15 } 
            }}
            exit={{ 
              opacity: 0, 
              scale: 0.95, 
              y: 10, 
              transition: { duration: 0.15, ease: "easeOut" } 
            }}
            className={cn(
              "relative z-50 w-full max-w-lg overflow-hidden rounded-2xl bg-card shadow-glass sm:w-[90%]",
              className
            )}
          >"""

replacement = """          <motion.div
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ 
              opacity: 1, 
              scale: 1, 
              transition: { type: "spring", bounce: 0.3, duration: 0.45 } 
            }}
            exit={{ 
              opacity: 0, 
              scale: 0.92, 
              transition: { type: "spring", bounce: 0, duration: 0.35 } 
            }}
            className={cn(
              "relative z-50 w-full max-w-lg overflow-hidden rounded-2xl bg-card shadow-glass sm:w-[90%]",
              className
            )}
          >"""

if target in content:
    with open('frontend/src/components/ui/Modal.tsx', 'w', encoding='utf-8') as f:
        f.write(content.replace(target, replacement))
    print("Modal replaced")
else:
    print("Target not found")
