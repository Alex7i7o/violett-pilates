with open('frontend/src/index.css', 'r', encoding='utf-8') as f:
    content = f.read()

scrollbar_css = '''
/* Apple Design Scrollbars */
* {
  scrollbar-width: thin;
  scrollbar-color: rgba(42, 28, 90, 0.2) transparent;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
  background-color: transparent;
}

::-webkit-scrollbar-track {
  background-color: transparent;
  border-radius: 9999px;
}

::-webkit-scrollbar-thumb {
  background-color: rgba(42, 28, 90, 0.2);
  border-radius: 9999px;
  border: 2px solid transparent;
  background-clip: padding-box;
}

::-webkit-scrollbar-thumb:hover {
  background-color: rgba(42, 28, 90, 0.4);
}
'''

if '/* Apple Design Scrollbars */' not in content:
    with open('frontend/src/index.css', 'a', encoding='utf-8') as f:
        f.write(scrollbar_css)
print('Scrollbar updated')
