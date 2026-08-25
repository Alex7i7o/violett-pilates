# -*- coding: utf-8 -*-
import re

def fix_modal(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'const [cachedTurno, setCachedTurno] = React.useState' in content:
        return

    # 1. Replace the early return
    content = content.replace(
        'if (!turno) return null',
        '''const [cachedTurno, setCachedTurno] = React.useState(turno)
  
  React.useEffect(() => {
    if (turno) setCachedTurno(turno)
  }, [turno])

  const displayTurno = turno || cachedTurno
  if (!displayTurno) return null'''
    )

    # 2. Replace uses of `turno` with `displayTurno` AFTER the hook
    # In CancelModal, we have `isLateCancellation` which uses `turno`. We need to use `displayTurno` there.
    # Actually, `useMemo(() => { if (!turno) return false; ... }, [turno])` should be updated to `displayTurno`.
    
    # We will just replace `turno.` with `displayTurno.` and `turno)` with `displayTurno)` where appropriate, 
    # but it's safer to just do a precise regex or manual replace.

    pass

# I'll just write the specific replacements for each file to be safe.
