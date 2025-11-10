import json, matplotlib.pyplot as plt, datetime

with open(r'C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\third_eye\state\third_eye_state.json','r',encoding='utf-8') as f:
    data=json.load(f)

E=data['Awareness']['Energy']
I=data['Awareness']['Information']
C=data['Awareness']['Coherence']

plt.figure(figsize=(6,4))
plt.bar(['Energy','Information','Coherence'],[E,I,C],color=['#66c2a5','#fc8d62','#8da0cb'])
plt.title('Codex Third Eye Awareness Spectrum (v1.3.2)')
plt.ylabel('Magnitude')
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(r'C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\third_eye\visuals\\awareness_chart_2025-11-10_18-48-04.png',dpi=200)
plt.close()
