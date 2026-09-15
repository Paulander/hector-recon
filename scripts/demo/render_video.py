"""Rasterize our restricted SVG vocabulary with Pillow, streaming bounded video."""
from functools import lru_cache
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

OUT=Path('/workspace/scratch/42ed9c9c2a4a/recon-demo')
HERE=Path(__file__).resolve().parent
S=1.6

@lru_cache(None)
def font(size):
    return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',round(size*S))

def color(value,opacity=1):
    if value in ('none','transparent'):return (0,0,0,0)
    v=value.lstrip('#')
    return tuple(int(v[i:i+2],16) for i in (0,2,4))+(round(255*opacity),)

def raster(svg):
    im=Image.new('RGB',(2560,1440),'#05070a'); draw=ImageDraw.Draw(im,'RGBA')
    def visit(e,opacity=1):
        a=e.attrib;op=opacity*float(a.get('opacity',1));tag=e.tag.rsplit('}',1)[-1]
        n=lambda key,default=0:float(a.get(key,default))*S
        if tag=='line':
            draw.line((n('x1'),n('y1'),n('x2'),n('y2')),fill=color(a['stroke'],op),width=max(1,round(n('stroke-width',1))))
        elif tag=='circle' and a.get('fill')!='transparent':
            x,y,r=n('cx'),n('cy'),n('r');draw.ellipse((x-r,y-r,x+r,y+r),fill=color(a.get('fill','#000000'),op))
        elif tag=='rect':
            x,y,w,h=n('x'),n('y'),n('width'),n('height');draw.rounded_rectangle((x,y,x+w,y+h),radius=n('rx'),fill=color(a.get('fill','#000000'),op))
        elif tag=='path':
            # The renderer emits only M x y, then three relative lines: a diamond.
            nums=list(map(float,re.findall(r'-?\d+(?:\.\d+)?(?:e[+-]?\d+)?',a['d'])))
            assert len(nums)==8
            x,y=nums[:2];points=[(x*S,y*S)]
            for dx,dy in zip(nums[2::2],nums[3::2]):x+=dx;y+=dy;points.append((x*S,y*S))
            draw.polygon(points,fill=color(a['fill'],op))
        elif tag=='text':
            stroke=round(n('stroke-width'));fill=color(a.get('fill','#edf3fa'),op)
            draw.text((n('x'),n('y')),e.text or '',font=font(float(a.get('font-size',16))),fill=fill,
                anchor='ms' if a.get('text-anchor')=='middle' else 'ls',stroke_width=stroke,
                stroke_fill=color(a.get('stroke',a.get('fill','#edf3fa')),op))
        for child in e:visit(child,op)
    visit(ET.fromstring(svg));return im

def main():
    kind=sys.argv[1];name='Hector-Growth.mp4' if kind=='growth' else 'Hector-Chess-Execution.mp4'
    processes=[]
    def timeout(*_):
        for p in processes:p.kill()
        raise TimeoutError('Video export exceeded 240 seconds')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(240)
    os.sched_setaffinity(0,{0,1})
    source=subprocess.Popen(['node',str(HERE/'render_media.js'),kind,'--svg-stream'],stdout=subprocess.PIPE,text=True)
    processes.append(source)
    encoder=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24',
        '-video_size','2560x1440','-framerate','24','-i','pipe:0','-an','-c:v','libx264','-threads','2',
        '-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/name)],stdin=subprocess.PIPE)
    processes.append(encoder)
    start=time.monotonic();count=0
    try:
        for line in source.stdout:
            im=raster(json.loads(line));encoder.stdin.write(im.tobytes())
            if count in (0,432,700):im.save(OUT/f'{kind}-video-frame-{count}.png')
            count+=1
            if count%120==0:print(kind,count,round(time.monotonic()-start,1),flush=True)
        encoder.stdin.close()
        assert source.wait()==0 and encoder.wait()==0
        assert count==(864 if kind=='growth' else 1008)
    finally:
        for p in processes:
            if p.poll() is None:p.kill()
    signal.alarm(0)
    print(name,count,round(time.monotonic()-start,2),flush=True)

if __name__=='__main__':main()
