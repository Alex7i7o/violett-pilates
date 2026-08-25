# -*- coding: utf-8 -*-
import re

with open('frontend/src/components/ui/Modal.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

target = """  React.useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => { document.body.style.overflow = 'unset' }
  }, [isOpen])"""

replacement = """  React.useEffect(() => {
    if (isOpen) {
      const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
      document.body.style.paddingRight = `${scrollbarWidth}px`;
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.paddingRight = '0px';
      document.body.style.overflow = 'unset';
    }
    return () => { 
      document.body.style.paddingRight = '0px';
      document.body.style.overflow = 'unset'; 
    }
  }, [isOpen])"""

if target in content:
    with open('frontend/src/components/ui/Modal.tsx', 'w', encoding='utf-8') as f:
        f.write(content.replace(target, replacement))
    print("Scrollbar shift fixed")
else:
    print("Target not found")
