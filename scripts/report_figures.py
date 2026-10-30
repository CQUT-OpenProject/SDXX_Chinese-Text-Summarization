"""Create vector diagrams for the course report from training state files."""
import json
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/report/assets'
OUT.mkdir(parents=True, exist_ok=True)


def box(c, x, y, w, h, lines, fill='#EEF3F7'):
    c.setFillColor(HexColor(fill)); c.setStrokeColor(HexColor('#3C5266'))
    c.roundRect(x, y, w, h, 4, fill=1, stroke=1)
    c.setFillColor(HexColor('#182734')); c.setFont('Helvetica', 9)
    for i, line in enumerate(lines):
        c.drawCentredString(x+w/2, y+h/2+(len(lines)-1)*6-i*12-3, line)


def arrow(c, x1, y1, x2, y2):
    import math
    c.setStrokeColor(HexColor('#3C5266')); c.setFillColor(HexColor('#3C5266'))
    c.line(x1, y1, x2, y2)
    a = math.atan2(y2-y1,x2-x1)
    path = c.beginPath(); path.moveTo(x2,y2)
    for t in (a+2.65,a-2.65):
        path.lineTo(x2+6*math.cos(t),y2+6*math.sin(t))
    path.close(); c.drawPath(path,fill=1,stroke=0)

c=canvas.Canvas(str(OUT/'bart-architecture.pdf'),pagesize=(500,180))
box(c,5,65,72,48,['Source text','Tokenizer'])
box(c,99,65,105,48,['Token + position','embeddings'])
box(c,226,65,112,48,['Encoder x 6','Self-attention + FFN'])
box(c,364,65,126,48,['Decoder x 6','Masked self-attention','Cross-attention + FFN'])
for x1,x2 in [(77,99),(204,226),(338,364)]: arrow(c,x1,89,x2,89)
box(c,233,4,105,37,['Previous tokens','+ positions'],'#FAF4E8')
arrow(c,338,22,423,65)
box(c,364,137,126,31,['Vocabulary projection'],'#FAF4E8')
arrow(c,427,113,427,137)
c.setFont('Helvetica',8); c.setFillColor(HexColor('#4A5965'))
c.drawString(234,118,'Encoder states: keys and values')
c.showPage(); c.save()

c=canvas.Canvas(str(OUT/'training-loss.pdf'),pagesize=(500,205))
colors={'2k':'#245A87','10k':'#B35B37'}
histories = {size: json.loads((ROOT/f'outputs/bart-{size}/trainer_state.json').read_text())['log_history'] for size in colors}
for panel,(kind,title) in enumerate([('train','Training loss: each 50 updates'),('eval','Validation loss: end of each epoch')]):
    x0=45+panel*245; y0=34; w=205; h=135
    import math
    key = 'loss' if kind == 'train' else 'eval_loss'
    all_values = [row[key] for history in histories.values() for row in history if key in row]
    step = .2 if kind == 'train' else .05
    lo = math.floor(min(all_values) / step) * step - step
    hi = math.ceil(max(all_values) / step) * step + step
    c.setStrokeColor(HexColor('#B0B9C0')); c.line(x0,y0,x0+w,y0); c.line(x0,y0,x0,y0+h)
    c.setFont('Helvetica',8); c.setFillColor(HexColor('#182734')); c.drawString(x0,183,title)
    for t in range(4):
        yv=lo+(hi-lo)*t/3; y=y0+(yv-lo)/(hi-lo)*h
        c.setStrokeColor(HexColor('#E1E5E8')); c.line(x0,y,x0+w,y)
        c.setFillColor(HexColor('#4A5965')); c.drawRightString(x0-5,y-3,f'{yv:.2f}')
    for e in range(4):
        x=x0+e/3*w; c.drawCentredString(x,y0-13,str(e))
    for size in ('2k','10k'):
        data=histories[size]
        vals=[(e['epoch'],e['loss' if kind=='train' else 'eval_loss']) for e in data if ('loss' if kind=='train' else 'eval_loss') in e]
        c.setStrokeColor(HexColor(colors[size])); c.setFillColor(HexColor(colors[size])); c.setLineWidth(1.0)
        points=[(x0+epoch/3*w,y0+(val-lo)/(hi-lo)*h) for epoch,val in vals]
        path=c.beginPath(); path.moveTo(*points[0])
        for x,y in points[1:]: path.lineTo(x,y)
        c.drawPath(path)
        if kind=='eval':
            for x,y in points: c.circle(x,y,2,fill=1,stroke=0)
    c.setFillColor(HexColor('#4A5965')); c.drawCentredString(x0+w/2,7,'Epoch')
for i,(size,color) in enumerate(colors.items()):
    c.setFillColor(HexColor(color)); c.rect(182+i*66,191,10,3,fill=1,stroke=0)
    c.setFillColor(HexColor('#182734')); c.setFont('Helvetica',8); c.drawString(195+i*66,189,size.upper())
c.showPage(); c.save()
