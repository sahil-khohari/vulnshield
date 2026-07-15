import re

with open('frontend/index.html', 'r') as f:
    content = f.read()

replacements = {
    r'bg-gray-100': 'bg-surface',
    r'bg-blue-600': 'bg-primary',
    r'bg-blue-50\b': 'bg-surface-alt',
    r'text-blue-700': 'text-primary-light',
    r'text-blue-500': 'text-accent',
    r'border-blue-200': 'border-surface-border',
    r'hover:bg-blue-700': 'hover:bg-accent-hover',
    r'hover:border-blue-500': 'hover:border-accent',
    r'ring-blue-500': 'ring-accent',
    r'text-blue-600': 'text-accent',
    r'bg-gray-50\b': 'bg-surface',
    r'text-gray-700': 'text-surface-text',
    r'text-gray-600': 'text-surface-text',
    r'text-gray-500': 'text-surface-muted',
    r'text-gray-400': 'text-surface-muted',
    r'border-gray-200': 'border-surface-border',
    r'bg-gray-800': 'bg-primary-light',
}

# Fix buttons specifically: they had bg-primary but we want bg-accent
# The header has bg-primary. 
# Buttons usually have `bg-primary hover:bg-accent-hover`. Wait, let's just do standard replace, then fix buttons.

# Let's fix buttons in a second pass:
for pattern, repl in replacements.items():
    content = re.sub(pattern, repl, content)

# Buttons should be accent colored, not primary (the header is primary).
# But wait, earlier bg-blue-600 was replaced with bg-primary.
# So buttons are now `bg-primary hover:bg-accent-hover text-white`. 
# We should change `bg-primary` to `bg-accent` ONLY for buttons.
content = content.replace('id="start-scanning-btn" class="bg-primary hover:bg-accent-hover', 'id="start-scanning-btn" class="bg-accent hover:bg-accent-hover')
content = content.replace('type="submit" id="start-scan-btn" class="bg-primary hover:bg-accent-hover', 'type="submit" id="start-scan-btn" class="bg-accent hover:bg-accent-hover')
content = content.replace('id="progress-bar" class="bg-primary', 'id="progress-bar" class="bg-accent')


with open('frontend/index.html', 'w') as f:
    f.write(content)

print("Done updating index.html")
