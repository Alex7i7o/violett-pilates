import re

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

if 'QueryClient' not in c:
    c = re.sub(r'^(import .*?;?\n)', r'\1import { QueryClient, QueryClientProvider } from "@tanstack/react-query";\n', c, count=1)
    
    app_comp = '''const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 60 * 5, // 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Toaster position="top-right" richColors />
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  )
}'''
    c = re.sub(r'function App\(\) \{\s*return \(\s*<BrowserRouter>\s*<Toaster[^>]+/>\s*<AppRoutes />\s*</BrowserRouter>\s*\)\s*\}', app_comp, c)
    
    with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
        f.write(c)

print("App.tsx wrapped")
