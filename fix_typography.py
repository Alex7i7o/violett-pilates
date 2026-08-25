with open('frontend/src/index.css', 'r', encoding='utf-8') as f:
    content = f.read()

apple_css = '''
/* Apple Design Typography & Materials */
h1, h2, h3, .text-xl, .text-2xl, .text-3xl {
  letter-spacing: -0.02em;
  font-optical-sizing: auto;
}

body {
  letter-spacing: 0.01em;
  line-height: 1.5;
}

/* Enhancing soft shadows for premium feel */
@theme {
  --shadow-soft: 0 4px 24px -6px rgba(42, 28, 90, 0.08);
  --shadow-glass: 0 16px 40px -12px rgba(42, 28, 90, 0.15);
}
'''
if 'Apple Design Typography' not in content:
    with open('frontend/src/index.css', 'a', encoding='utf-8') as f:
        f.write(apple_css)
print('Typography updated')
