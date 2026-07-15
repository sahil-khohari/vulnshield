import re

with open('frontend/index.html', 'r') as f:
    content = f.read()

# Replace classes
replacements = {
    r'body class="bg-surface"': 'body class="bg-background text-text"',
    r'header class="bg-primary text-white shadow-lg"': 'header class="bg-surface text-text border-b border-border shadow-lg"',
    r'footer class="bg-primary-light text-white py-8 mt-auto"': 'footer class="bg-surface text-text border-t border-border py-8 mt-auto"',
    r'bg-white': 'bg-surface border border-border',
    r'bg-surface-alt': 'bg-background border border-border',
    r'text-primary-light': 'text-text',
    r'text-surface-text': 'text-text-secondary',
    r'text-surface-muted': 'text-text-secondary',
    r'bg-accent\b': 'bg-primary',
    r'hover:bg-accent-hover': 'hover:bg-primary-hover',
    r'border-surface-border': 'border-border',
    r'ring-accent': 'ring-primary',
}

for pattern, repl in replacements.items():
    content = re.sub(pattern, repl, content)

# Since we blindly replaced bg-accent with bg-primary, let's fix any SVG icons that should be text-accent. 
# They were already text-accent, which we didn't replace, so they are fine.

with open('frontend/index.html', 'w') as f:
    f.write(content)

print("Done updating index.html")
