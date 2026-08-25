# -*- coding: utf-8 -*-
with open('frontend/src/components/booking/BookingGrid.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

target = """            return (
              <button
                key={date}
                onClick={() => setActiveDate(date)}
                className={`snap-start relative flex flex-col items-center justify-center min-w-[100px] px-4 py-3 rounded-2xl transition-all duration-300 ${
                  isActive 
                    ? 'bg-violett-900 text-white shadow-lg' 
                    : 'bg-white text-muted hover:bg-violett-50'
                }`}
              >
                <span className="font-semibold">{formatTabDate(date)}</span>
                <span className={`text-xs mt-1 px-2 py-0.5 rounded-full ${
                  isActive ? 'bg-white/20 text-white' : availableSpots > 0 ? 'bg-violett-100 text-violett-900' : 'bg-red-100 text-red-900'
                }`}>
                  {availableSpots > 0 ? `${availableSpots} cupos` : 'Agotado'}
                </span>
                
                {isActive && (
                  <motion.div 
                    layoutId="activeTab"
                    className="absolute inset-0 border-2 border-violett-900 rounded-2xl pointer-events-none"
                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                  />
                )}
              </button>
            )"""

replacement = """            return (
              <button
                key={date}
                onClick={() => setActiveDate(date)}
                className={`snap-start relative flex flex-col items-center justify-center min-w-[100px] px-4 py-3 rounded-2xl transition-colors duration-200 z-10 ${
                  isActive 
                    ? 'text-white' 
                    : 'bg-white text-muted hover:bg-violett-50'
                }`}
              >
                {isActive && (
                  <motion.div 
                    layoutId="activeDateTabPill"
                    className="absolute inset-0 bg-violett-900 rounded-2xl shadow-lg"
                    style={{ zIndex: -1 }}
                    transition={{ type: "spring", bounce: 0.15, duration: 0.5 }}
                  />
                )}
                
                <span className="font-semibold">{formatTabDate(date)}</span>
                <span className={`text-xs mt-1 px-2 py-0.5 rounded-full transition-colors duration-200 ${
                  isActive ? 'bg-white/20 text-white' : availableSpots > 0 ? 'bg-violett-100 text-violett-900' : 'bg-red-100 text-red-900'
                }`}>
                  {availableSpots > 0 ? `${availableSpots} cupos` : 'Agotado'}
                </span>
              </button>
            )"""

if target in content:
    with open('frontend/src/components/booking/BookingGrid.tsx', 'w', encoding='utf-8') as f:
        f.write(content.replace(target, replacement))
    print("Tabs fixed")
else:
    print("Target not found")
