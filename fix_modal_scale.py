# -*- coding: utf-8 -*-
import re

with open('frontend/src/components/ui/Modal.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

target_backdrop = """          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1, transition: { duration: 0.3, ease: "easeOut" } }}
            exit={{ opacity: 0, transition: { duration: 0.5, ease: "easeInOut" } }}
            className="fixed inset-0 bg-violett-900/40 backdrop-blur-sm"
            onClick={onClose}
          />"""

replacement_backdrop = """          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1, transition: { duration: 0.3, ease: "easeOut" } }}
            exit={{ opacity: 0, transition: { duration: 0.35, ease: "easeInOut" } }}
            className="fixed inset-0 bg-violett-900/40 backdrop-blur-sm"
            onClick={onClose}
          />"""

target_modal = """            exit={{ 
              opacity: 0, 
              scale: 0.75, 
              transition: { type: "spring", bounce: 0, duration: 0.5 } 
            }}"""

replacement_modal = """            exit={{ 
              opacity: 0, 
              scale: 0.92, 
              transition: { type: "spring", bounce: 0, duration: 0.35 } 
            }}"""

if target_backdrop in content and target_modal in content:
    content = content.replace(target_backdrop, replacement_backdrop)
    content = content.replace(target_modal, replacement_modal)
    with open('frontend/src/components/ui/Modal.tsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Modal scale restored")
else:
    print("Targets not found")
