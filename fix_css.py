with open('frontend/src/index.css', 'r', encoding='utf-8') as f:
    content = f.read()

animation_css = '''
@keyframes shimmer {
  100% {
    transform: translateX(100%);
  }
}
.animate-shimmer {
  animation: shimmer 1.5s infinite;
}
'''
if '@keyframes shimmer' not in content:
    with open('frontend/src/index.css', 'a', encoding='utf-8') as f:
        f.write(animation_css)
print('CSS updated')
