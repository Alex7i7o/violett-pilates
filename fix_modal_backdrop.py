# -*- coding: utf-8 -*-
import re

with open('frontend/src/components/ui/Modal.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

target = """          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1, transition: { duration: 0.25, ease: "easeOut" } }}
            exit={{ opacity: 0, transition: { duration: 0.15, ease: "linear" } }}
            className="fixed inset-0 bg-violett-900/40 backdrop-blur-sm"
            onClick={onClose}
          />"""

replacement = """          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1, transition: { duration: 0.3, ease: "easeOut" } }}
            exit={{ opacity: 0, transition: { duration: 0.3, ease: "easeInOut" } }}
            className="fixed inset-0 bg-violett-900/40 backdrop-blur-sm"
            onClick={onClose}
          />"""

if target in content:
    with open('frontend/src/components/ui/Modal.tsx', 'w', encoding='utf-8') as f:
        f.write(content.replace(target, replacement))
    print("Backdrop replaced")
else:
    print("Backdrop Target not found")
