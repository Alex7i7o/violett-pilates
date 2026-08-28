import os
import re

files_to_update = [
    'frontend/src/layouts/AdminLayout.tsx',
    'frontend/src/layouts/ProfesorLayout.tsx'
]

for filepath in files_to_update:
    if not os.path.exists(filepath):
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add mobile state
    if "isMobileMenuOpen" not in content:
        content = content.replace("const navigate = useNavigate();", "const navigate = useNavigate();\n  const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false);")

    # Add close on route change
    if "React.useEffect(() => {" not in content and "isMobileMenuOpen" in content:
        content = content.replace("const location = useLocation();", "const location = useLocation();\n  React.useEffect(() => { setIsMobileMenuOpen(false); }, [location.pathname]);")

    # Change aside to be hidden on mobile
    content = content.replace('<aside className="w-64 bg-card', '<aside className="hidden lg:flex w-64 shrink-0 bg-card')
    
    # Add Hamburger button to header
    hamburger = """
        <header className="px-4 lg:px-8 py-4 lg:py-6 flex items-center justify-between lg:justify-end border-b lg:border-none border-violett-100 bg-background sticky top-0 z-10">
          <button 
            onClick={() => setIsMobileMenuOpen(true)}
            className="lg:hidden p-2 text-violett-900 rounded-lg hover:bg-violett-50"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
          </button>
"""
    # Replace header start
    content = re.sub(r'<header className="[^"]+ flex items-center justify-end">', hamburger.strip(), content)

    # Add Mobile Menu JSX right before </main>
    mobile_menu_jsx = """
      <AnimatePresence>
        {isMobileMenuOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsMobileMenuOpen(false)}
              className="fixed inset-0 bg-black/40 z-40 lg:hidden backdrop-blur-sm"
            />
            <motion.aside
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', bounce: 0, duration: 0.4 }}
              className="fixed top-0 left-0 bottom-0 w-64 bg-card z-50 flex flex-col border-r border-violett-100 shadow-2xl lg:hidden"
            >
              <div className="p-6 pb-2 flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-violett-900 flex items-center justify-center text-white font-bold italic">V</div>
                  <span className="font-bold text-xl text-violett-900 tracking-tight">Violett</span>
                </div>
                <button onClick={() => setIsMobileMenuOpen(false)} className="text-muted hover:text-foreground">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
              <h2 className="px-6 text-sm font-semibold text-muted uppercase tracking-wider mt-2 mb-4">Menú</h2>
              <nav className="flex-1 overflow-y-auto">
                <ul className="flex flex-col gap-1 px-3">
                  {navItems.map((item) => {
                    const isActive = location.pathname.startsWith(item.path);
                    return (
                      <li key={item.name}>
                        <Link
                          to={item.path}
                          className={`block py-3 px-4 rounded-xl text-sm transition-all ${
                            isActive 
                              ? 'text-violett-900 font-bold bg-violett-100 shadow-sm' 
                              : 'text-muted hover:bg-violett-50 hover:text-foreground'
                          }`}
                        >
                          {item.name}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </nav>
              <div className="p-4 border-t border-violett-100">
                <button 
                  onClick={handleLogout}
                  className="w-full py-3 px-4 text-sm font-medium text-rose-600 hover:bg-rose-50 rounded-xl transition-colors text-left"
                >
                  Cerrar Sesión
                </button>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    """
    
    if "isMobileMenuOpen &&" not in content:
        content = content.replace("</main>", mobile_menu_jsx + "\n      </main>")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Layouts updated for mobile")
