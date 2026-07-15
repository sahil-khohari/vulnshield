import re

with open('frontend/css/styles.css', 'r') as f:
    content = f.read()

content = content.replace('#3b82f6', '#0f766e')
content = content.replace('rgba(59, 130, 246', 'rgba(15, 118, 110')

with open('frontend/css/styles.css', 'w') as f:
    f.write(content)

print("Done updating styles.css")
