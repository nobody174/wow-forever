import sys
from PIL import Image,ImageDraw,ImageFont
d,az,fonts,out=sys.argv[1:5]
I=lambda n:Image.open(f"{d}/frost_{n}.png").convert("RGBA")
def s9(img,w,h,c):
    W,H=img.size;o=Image.new("RGBA",(w,h))
    xs=[(0,c,0,c),(c,w-c,c,W-c),(w-c,w,W-c,W)];ys=[(0,c,0,c),(c,h-c,c,H-c),(h-c,h,H-c,H)]
    for a in xs:
        for b in ys:
            if a[1]>a[0] and b[1]>b[0]:o.alpha_composite(img.crop((a[2],b[2],a[3],b[3])).resize((a[1]-a[0],b[1]-b[0]),Image.BILINEAR),(a[0],b[0]))
    return o
F=lambda s,f="Barlow-500.ttf":ImageFont.truetype(f"{fonts}/{f}",s)
W,H=820,664;im=Image.new("RGBA",(W,H))
# board window gradient 140deg #14163a -> #0a0a1d -> #07070f
import numpy as np
yy,xx=np.mgrid[0:H,0:W];t=np.clip((xx*0.643+yy*0.766)/(W*0.643+H*0.766),0,1)
c0,c1,c2=np.array([20,22,58]),np.array([10,10,29]),np.array([7,7,15])
col=np.where(t[...,None]<.55,c0+(c1-c0)*(t[...,None]/.55),c1+(c2-c1)*((t[...,None]-.55)/.45))
im=Image.fromarray(np.dstack([col,np.full((H,W),255)]).astype(np.uint8),"RGBA")
p=I("panel").copy()
tile=Image.new("RGBA",(W,H),(0,0,0,0))
for x in range(0,W,256):
    for y in range(0,H,256):tile.alpha_composite(p,(x,y))
tm=np.asarray(tile,float);base=np.array([12,13,34.]);star=(np.abs(tm[...,:3]-base).sum(-1)>20)
sa=Image.fromarray((star*230).astype(np.uint8));st=Image.new("RGBA",(W,H),(255,255,255,0));st.putalpha(sa);im.alpha_composite(Image.composite(tile,Image.new("RGBA",(W,H),(0,0,0,0)),sa))
im.alpha_composite(I("glow_violet").resize((330,330)),(-60,H-300));im.alpha_composite(I("glow_cyan").resize((330,330)),(W-300,-120))
im.alpha_composite(s9(I("frame"),W,H,32),(0,0));dr=ImageDraw.Draw(im)
dr.text((36,26),"R O A D   T O   F O R E V E R",font=F(14),fill="#F2F4FF")
names=["home","plan","talents","gear","macros","tweaks"];lab=["Home","Launch plan","Builds & talents","Gear (Mr.BiZ)","Macros","Gameplay"]
im.alpha_composite(I("link_fade").resize((8,40)),(30+9,100+15+9)) if False else None
for i,n in enumerate(names):
    y=100+i*28+(i>=2)*0;cx,cy=45,y+13
    st="on" if i==0 else("hover" if i==3 else "normal")
    o=I("orb_"+st).resize((44,44),Image.LANCZOS);im.alpha_composite(o,(cx-22,cy-22))
    ic=Image.open(f"{az}/azeroth_icon_{n}.png").convert("RGBA").resize((14,14),Image.LANCZOS)
    t2=Image.new("RGBA",ic.size,((127,231,255) if st!="normal" else (169,176,214))+(255,));t2.putalpha(ic.getchannel("A"));im.alpha_composite(t2,(cx-7,cy-7))
    dr.text((cx+32,cy),lab[i],font=F(14),fill="#F2F4FF" if st!="normal" else "#A9B0D6",anchor="lm")
for i in range(5):im.alpha_composite(I("link").resize((8,28)),(cx-4,100+13+i*28))
im.alpha_composite(s9(I("glass"),420,300,16),(260,90))
im.alpha_composite(s9(I("display"),300,150,16),(320,120))
dr.text((470,195),"18",font=F(60,"ChakraPetch-700.ttf"),fill="#F2F4FF",anchor="mm")
for i,k in enumerate(["normal","hover","primary","primary_hover","disabled"]):
    x=260+i*150;im.alpha_composite(s9(I("btn_"+k),128,32,16),(x,420))
    dr.text((x+64,436),k.replace("_"," "),font=F(13),fill="#fff" if "primary" in k else "#F2F4FF",anchor="mm")
im.alpha_composite(I("check_off"),(260,480));im.alpha_composite(I("check_on"),(300,480))
for i,st in enumerate(["off","on"]):
    x=360+i*70;im.alpha_composite(I("switch_"+st).resize((44,22)),(x,486))
    im.alpha_composite(I("switch_knob_"+st).resize((22,22)),(x+(21 if st=="on" else 1),486))
im.alpha_composite(s9(I("slider_track"),300,16,8),(260,550))
im.alpha_composite(I("slider_fill").resize((300,16)).crop((0,0,210,16)),(260,550))
im.alpha_composite(I("slider_knob"),(260+210-16,542))
im.convert("RGB").save(out)
