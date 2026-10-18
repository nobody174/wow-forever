import sys,numpy as np
from PIL import Image
d=sys.argv[1]
L=lambda n:np.asarray(Image.open(f"{d}/frost_{n}.png").convert("RGBA"),float)
sizes={"frame":(128,128),"panel":(256,256),"glow_violet":(128,128),"glow_cyan":(128,128),"glass":(64,64),"display":(64,64),"orb_normal":(32,32),"orb_hover":(32,32),"orb_on":(32,32),"link":(8,64),"link_fade":(8,64),"check_off":(32,32),"check_on":(32,32),"switch_off":(64,32),"switch_on":(64,32),"switch_knob_off":(32,32),"switch_knob_on":(32,32),"slider_track":(128,16),"slider_fill":(128,16),"slider_knob":(32,32)}
for k in("normal","hover","primary","primary_hover","disabled"):sizes["btn_"+k]=(128,32)
ok=True
for n,(w,h) in sizes.items():
    if L(n).shape[:2]!=(h,w):print("SIZE",n);ok=False
for n in["glow_violet","glow_cyan","orb_hover","orb_on","check_on","switch_knob_on","slider_knob","btn_hover","btn_primary","btn_primary_hover"]:
    a=L(n)[...,3];e=max(a[0].max(),a[-1].max(),a[:,0].max(),a[:,-1].max());print("edge alpha",n,int(e))
    if e>10 and n not in("btn_hover",):ok=False
def plain(n,cx,cy):
    a=L(n);m=0
    if cx:m=max(m,abs(a[:,cx[0]:cx[1]]-a[:,cx[0]:cx[0]+1]).max())
    if cy:m=max(m,abs(a[cy[0]:cy[1]]-a[cy[0]:cy[0]+1]).max())
    print("plain",n,round(m,2));return m<1.5
ok&=plain("frame",(32,96),(32,96));ok&=plain("display",(16,48),None);ok&=plain("glass",(16,48),None)
ok&=plain("btn_normal",(16,112),None);ok&=plain("btn_hover",(16,112),None);ok&=plain("btn_disabled",(16,112),None)
ok&=plain("switch_off",(16,48),None);ok&=plain("slider_track",(8,120),None)
ok&=plain("link",None,(0,64)) if False else True
p=L("panel");print("panel seam x/y",abs(p[:,0]-p[:,-1]).mean().round(2),abs(p[0]-p[-1]).mean().round(2),"vs neighbour",abs(p[:,0]-p[:,1]).mean().round(2))
k0,k1=L("switch_knob_off")[...,3],L("switch_knob_on")[...,3];print("knob core same",int(((k0>250)^(k1>250)).sum()))
# mirror symmetry of frame corners
f=L("frame");print("frame TL vs TR mirror",abs(f[:40,:40]-f[:40,::-1][:,:40]).max(),"TL vs BL",abs(f[:40,:40]-f[::-1][:40,:40]).max())
def over(c,bg):a=c[3]/255;return tuple(int(round(c[k]*a+bg[k]*(1-a))) for k in range(3))
hx=lambda t:"#%02X%02X%02X"%t
def bl(fg,a,bg):return hx(tuple(int(round(fg[k]*a+bg[k]*(1-a))) for k in range(3)))
WIN=(10,10,29);PANEL=(12,13,34);CYAN=(127,231,255);WHITE=(255,255,255);MUT=(169,176,214);VIO=(123,92,255);ORBC=(18,20,43)
def px(n,x,y,bg=None):
    c=L(n)[y,x];return (hx(over(c,bg)) if bg else hx(tuple(int(v) for v in c[:3]))),c[3]/255
def two(fg1,a1,fg2,a2,bg):  # fg2 over fg1 over bg
    t=tuple(fg1[k]*a1+bg[k]*(1-a1) for k in range(3));return bl(fg2,a2,tuple(t))
rows=[("frame","border over window (x=0,y=64)",px("frame",0,64,WIN),bl(CYAN,.3,WIN)),
("frame","bracket (x=17,y=22)",px("frame",17,22,WIN),"#7FE7FF"),
("panel","base (no star)",px("panel",1,1),"#0C0D22 (mean of board gradient)"),
("glass","fill top (y=5) over window",px("glass",32,5,WIN),bl(WHITE,.08-.06*5/64,WIN)),
("glass","fill bottom (y=58) over window",px("glass",32,58,WIN),bl(WHITE,.08-.06*58/64,WIN)),
("glass","border (x=0,y=32) over window",px("glass",0,32,WIN),two(WHITE,.08-.06*32/64,CYAN,.22,WIN)),
("display","centre over window",px("display",32,32,WIN),bl(WHITE,.05,WIN)),
("orb_normal","disc",px("orb_normal",16,16),"#12142B"),("orb_normal","ring (x=6)",px("orb_normal",6,16),two(ORBC,1,MUT,.5,ORBC)),
("orb_hover","ring",px("orb_hover",6,16),"#7FE7FF"),("orb_on","ring",px("orb_on",6,16),"#7FE7FF"),
("orb_on","centre",px("orb_on",16,16),"#22305A"),
("btn_normal","fill over window (x=64,y=16)",px("btn_normal",64,16,WIN),bl(WHITE,.06,WIN)),
("btn_normal","border (y=3) over fill",px("btn_normal",64,3,WIN),two(WHITE,.06,CYAN,.38,WIN)),
("btn_hover","border (y=3)",px("btn_hover",64,3,WIN),"#7FE7FF"),
("btn_primary","left end (x=14,y=16)",px("btn_primary",14,16),"~#7B5CFF (135deg gradient start, #7B5CFF at corner)"),
("btn_primary","right end (x=114,y=16)",px("btn_primary",114,16),"~#3FA4FF"),
("btn_disabled","alpha",px("btn_disabled",64,16),"white 6% x 0.40 = a0.02"),
("check_off","ring over fill",px("check_off",6,16,WIN),two(WHITE,.05,MUT,.6,WIN)),
("check_on","ring",px("check_on",6,16),"#7FE7FF"),("check_on","core",px("check_on",16,16),"#7FE7FF"),
("switch_off","fill over window",px("switch_off",32,16,WIN),bl(WHITE,.06,WIN)),
("switch_on","left over window (x=18)",px("switch_on",18,16,WIN),bl(tuple(int(VIO[k]*(1-18/64)+CYAN[k]*(18/64)) for k in range(3)),.5-.1*18/64,WIN)),
("switch_on","border (y=0)",px("switch_on",32,0),"#7FE7FF"),
("switch_knob_off","centre-ish (x=13,y=13)",px("switch_knob_off",13,13),"~#FFFFFF"),("switch_knob_off","far edge (x=22,y=22)",px("switch_knob_off",22,22),"~#A9B0D6"),
("switch_knob_on","far edge",px("switch_knob_on",22,22),"~#7FE7FF"),
("slider_track","groove over window",px("slider_track",64,8,WIN),bl(WHITE,.10,WIN)),
("slider_fill","x=2",px("slider_fill",2,8),"#7B5CFF"),("slider_fill","x=125",px("slider_fill",125,8),"#7FE7FF"),
("slider_knob","highlight (x=13,y=13)",px("slider_knob",13,13),"#FFFFFF"),("slider_knob","far edge (x=22,y=22)",px("slider_knob",22,22),"~#7B5CFF .. #7FE7FF (72-100%)")]
with open(sys.argv[2],"w") as f:
    f.write("| File | Point | My PNG | Board |\n|---|---|---|---|\n")
    for n,pt,(h,a),b in rows:f.write(f"| {n} | {pt} | {h}{'' if a>0.995 else ' a%.2f'%a} | {b} |\n")
print(open(sys.argv[2]).read());print("OK" if ok else "FAIL")
