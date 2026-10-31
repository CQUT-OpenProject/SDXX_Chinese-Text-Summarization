"""Create vector diagrams for the course report from training state files."""
import json
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

font_paths = list(Path("/System/Library/AssetsV2").glob("com_apple_MobileAsset_Font*/**/STFANGSO.ttf"))
if not font_paths:
    raise FileNotFoundError("缺少 STFANGSO.ttf；请配置可用的中文 TrueType 字体")
pdfmetrics.registerFont(TTFont("ReportChinese", str(font_paths[0])))

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/report-figures'
OUT.mkdir(parents=True, exist_ok=True)


def box(c, x, y, w, h, lines, fill='#EEF3F7'):
    c.setFillColor(HexColor(fill)); c.setStrokeColor(HexColor('#3C5266'))
    c.roundRect(x, y, w, h, 4, fill=1, stroke=1)
    c.setFillColor(HexColor('#182734')); c.setFont('ReportChinese', 9)
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
box(c,5,65,72,48,['输入原文','词元化'])
box(c,99,65,105,48,['词元嵌入','＋位置嵌入'])
box(c,226,65,112,48,['编码器 × 6','自注意力＋前馈网络'])
box(c,364,65,126,48,['解码器 × 6','掩码自注意力','交叉注意力＋前馈网络'])
for x1,x2 in [(77,99),(204,226),(338,364)]: arrow(c,x1,89,x2,89)
box(c,233,4,105,37,['已生成词元','＋位置嵌入'],'#FAF4E8')
arrow(c,338,22,423,65)
box(c,364,137,126,31,['词表投影与预测'],'#FAF4E8')
arrow(c,427,113,427,137)
c.setFont('ReportChinese',8); c.setFillColor(HexColor('#4A5965'))
c.drawString(234,118,'编码器输出作为键和值')
c.showPage(); c.save()

c=canvas.Canvas(str(OUT/'training-loss.pdf'),pagesize=(500,205))
colors={'2k':'#245A87','10k':'#B35B37'}
histories = {size: json.loads((ROOT/f'docs/experiment-data/bart-{size}-trainer_state.json').read_text())['log_history'] for size in colors}
for panel,(kind,title) in enumerate([('train','训练损失（每 50 步）'),('eval','验证损失（每轮结束）')]):
    x0=45+panel*245; y0=34; w=205; h=135
    import math
    key = 'loss' if kind == 'train' else 'eval_loss'
    all_values = [row[key] for history in histories.values() for row in history if key in row]
    step = .2 if kind == 'train' else .05
    lo = math.floor(min(all_values) / step) * step - step
    hi = math.ceil(max(all_values) / step) * step + step
    c.setStrokeColor(HexColor('#B0B9C0')); c.line(x0,y0,x0+w,y0); c.line(x0,y0,x0,y0+h)
    c.setFont('ReportChinese',9); c.setFillColor(HexColor('#182734')); c.drawString(x0,183,title)
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
    c.setFillColor(HexColor('#4A5965')); c.setFont('ReportChinese',8); c.drawCentredString(x0+w/2,7,'训练轮次')
for i,(size,color) in enumerate(colors.items()):
    c.setFillColor(HexColor(color)); c.rect(182+i*66,191,10,3,fill=1,stroke=0)
    c.setFillColor(HexColor('#182734')); c.setFont('Helvetica',8); c.drawString(195+i*66,189,size.upper())
c.showPage(); c.save()
