import re

file_path = 'frontend_v2/src/components/IntroVideo.jsx'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Make the button subtle, transparent, and not distracting as per instructions.
new_button = """<button
          onClick={onComplete}
          className="w-full max-w-xs py-2 clip-hex bg-transparent border border-white/10 text-white/30 font-orbitron tracking-widest text-xs hover:bg-white/10 hover:text-white/80 transition-all uppercase"
        >
          [ ПРОПУСТИТЬ ]
        </button>"""

content = re.sub(r'<button[\s\S]*?>[\s\S]*?\[ ПРОПУСТИТЬ \][\s\S]*?</button>', new_button, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("IntroVideo.jsx patched.")
