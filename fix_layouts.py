import os
import re

def update_file(path, replacements):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# 1. Update AdminLayout
admin_repl = [
    ("import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';", 
     "import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';\nimport { motion, AnimatePresence } from 'framer-motion';"),
    ("<Outlet />",
     """<AnimatePresence mode="wait">
            <motion.div 
              key={location.pathname}
              initial={{ opacity: 0, y: 10, filter: 'blur(4px)' }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)', transition: { duration: 0.4, ease: [0.32, 0.72, 0, 1] } }}
              exit={{ opacity: 0, filter: 'blur(4px)', transition: { duration: 0.15 } }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>"""),
]
update_file('frontend/src/layouts/AdminLayout.tsx', admin_repl)

# 2. Update ProfesorLayout
profesor_repl = [
    ("import { Outlet, useNavigate } from 'react-router-dom';",
     "import { Outlet, useNavigate, useLocation } from 'react-router-dom';\nimport { motion, AnimatePresence } from 'framer-motion';"),
    ("export function ProfesorLayout() {",
     "export function ProfesorLayout() {\n  const location = useLocation();"),
    ('className="bg-card shadow-sm border-b border-violett-100 sticky top-0 z-40"',
     'className="bg-white/70 backdrop-blur-xl saturate-150 border-b border-violett-100/50 shadow-sm sticky top-0 z-40"'),
    ("<Outlet />",
     """<AnimatePresence mode="wait">
            <motion.div 
              key={location.pathname}
              initial={{ opacity: 0, y: 10, filter: 'blur(4px)' }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)', transition: { duration: 0.4, ease: [0.32, 0.72, 0, 1] } }}
              exit={{ opacity: 0, filter: 'blur(4px)', transition: { duration: 0.15 } }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>"""),
]
update_file('frontend/src/layouts/ProfesorLayout.tsx', profesor_repl)

# 3. Update App.tsx (Client Dashboard)
app_repl = [
    ("import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'",
     "import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'\nimport { motion, AnimatePresence } from 'framer-motion'"),
    ('className="bg-card shadow-sm border-b border-violet-100 sticky top-0 z-40"',
     'className="bg-white/70 backdrop-blur-xl saturate-150 border-b border-violett-100/50 shadow-sm sticky top-0 z-40"'),
    ("function AppRoutes() {",
     "function AppRoutes() {\n  const location = useLocation()"),
    ("<Dashboard />",
     """<AnimatePresence mode="wait">
              <motion.div 
                key={location.pathname}
                initial={{ opacity: 0, y: 10, filter: 'blur(4px)' }}
                animate={{ opacity: 1, y: 0, filter: 'blur(0px)', transition: { duration: 0.4, ease: [0.32, 0.72, 0, 1] } }}
                exit={{ opacity: 0, filter: 'blur(4px)', transition: { duration: 0.15 } }}
              >
                <Dashboard />
              </motion.div>
            </AnimatePresence>"""),
]
update_file('frontend/src/App.tsx', app_repl)

print("Layouts updated with page transitions and glassmorphism.")
