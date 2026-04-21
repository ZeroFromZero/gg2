with open('app.py', encoding='utf-8') as f:
    c = f.read()

old = 'fb = "C:/Windows/Fonts/arialbd.ttf"\n    fr = "C:/Windows/Fonts/arial.ttf"'
new = 'fb = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "fonts", "bold.ttf")\n    fr = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "fonts", "regular.ttf")'

count = c.count(old)
print(f'Found {count} occurrences')
c = c.replace(old, new)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')
