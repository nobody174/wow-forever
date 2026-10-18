import sys,numpy as np
from PIL import Image
d=sys.argv[1]
L=lambda n:np.asarray(Image.open(f"{d}/obsidian_{n}.png").convert("RGBA"),float)
ok=True
sizes={"frame":(128,128),"plate":(128,128),"tab_hover":(64,32),"tab_on":(64,32),"tab_sep":(8,32),"btn_normal":(128,32),"btn_hover":(128,32),"btn_primary":(128,32),"btn_primary_hover":(128,32),"btn_disabled":(128,32),"check_off":(32,32),"check_on":(32,32),"switch_off":(64,32),"switch_on":(64,32),"switch_knob_off":(32,32),"switch_knob_on":(32,32),"slider_track":(128,16),"slider_fill":(128,16),"slider_knob":(32,32),"display":(64,64)}
for n,(w,h) in sizes.items():
    a=L(n)
    if a.shape[:2]!=(h,w):print("SIZE",n);ok=False
# glow pieces must not touch canvas edge
for n in["tab_on","btn_hover","btn_primary","btn_primary_hover","check_on","switch_knob_on","slider_knob"]:
    a=L(n)[...,3];e=max(a[0].max(),a[-1].max(),a[:,0].max(),a[:,-1].max())
    print("edge alpha",n,int(e))
    lim={'btn_hover':33,'btn_primary_hover':45,'tab_on':22,'btn_primary':3}.get(n,3)
    if e>lim:ok=False
def plain(n,cx,cy):
    a=L(n);m=0
    if cx:m=max(m,abs(a[:,cx[0]:cx[1]]-a[:,cx[0]:cx[0]+1]).max())
    if cy:m=max(m,abs(a[cy[0]:cy[1]]-a[cy[0]:cy[0]+1]).max())
    print("plain",n,m);return m<1.5
for n in["frame","plate"]:ok&=plain(n,(24,104),(24,104))
for n in["btn_normal","btn_hover","btn_primary","btn_primary_hover","btn_disabled","tab_hover","tab_on"]:ok&=plain(n,(12,52) if n.startswith("tab") else (12,116),None)
ok&=plain("display",(16,48),(16,48));ok&=plain("slider_track",(8,120),None);ok&=plain("slider_fill",(8,120),None);ok&=plain("switch_off",(16,48),None);ok&=plain("switch_on",(16,48),None)
def over(c,bg):  # composite RGBA pixel over bg
    a=c[3]/255;return tuple(int(round(c[k]*a+bg[k]*(1-a))) for k in range(3))
hx=lambda t:"#%02X%02X%02X"%t
W=(14,15,19);CD=(23,26,33)
def px(n,x,y,bg=None):
    c=L(n)[y,x];return hx(over(c,bg) if bg else tuple(int(v) for v in c[:3])), c[3]/255
def blend(fg,a,bg):return hx(tuple(int(round(fg[k]*a+bg[k]*(1-a))) for k in range(3)))
rows=[("frame","border (x=0,y=64)",px("frame",0,64),"#2A2F3A"),
("plate","fill",px("plate",64,64),"#171A21"),("plate","border (x=0,y=64)",px("plate",0,64),"#2A2F3A"),
("plate","top inner edge (y=1)",px("plate",64,1),blend((255,255,255),.05,CD)),
("tab_hover","fill",px("tab_hover",32,16),"#171A21"),
("tab_on","fill over window",px("tab_on",32,8,W),blend((53,214,196),.08,W)),
("tab_on","underline",px("tab_on",32,26,W),"#35D6C4"),
("btn_normal","fill",px("btn_normal",64,16),"#1C2029"),("btn_normal","border (y=3)",px("btn_normal",64,3),"#2A2F3A"),
("btn_hover","border (y=3)",px("btn_hover",64,3),"#35D6C4"),("btn_hover","ring (y=1) over window",px("btn_hover",64,1,W),blend((53,214,196),.12,W)),
("btn_primary","border (y=3)",px("btn_primary",64,3),"#35D6C4"),("btn_primary","fill over card",px("btn_primary",64,16,CD),blend((53,214,196),.10,CD)),
("btn_disabled","fill alpha (40%)",px("btn_disabled",64,16),"#1C2029 @0.40"),
("check_off","fill",px("check_off",16,16),"#12151B"),("check_off","border (x=3)",px("check_off",3,16),"#3A4150"),
("check_on","fill",px("check_on",6,16),"#35D6C4"),("check_on","tick",px("check_on",14,20),"#0E0F13"),
("switch_off","fill",px("switch_off",32,16),"#12151B"),("switch_off","border (y=0)",px("switch_off",32,0),"#3A4150"),
("switch_on","fill over window",px("switch_on",32,16,W),blend((53,214,196),.2,W)),("switch_on","border (y=0)",px("switch_on",32,0),"#35D6C4"),
("switch_knob_off","disc",px("switch_knob_off",16,16),"#8A91A3"),("switch_knob_on","disc",px("switch_knob_on",16,16),"#35D6C4"),
("slider_track","groove",px("slider_track",64,8),"#2A2F3A"),("slider_fill","fill",px("slider_fill",64,8),"#35D6C4"),
("slider_knob","centre-ish (lit)",px("slider_knob",13,13),"~#FFFFFF (highlight stop)"),("slider_knob","far rim (x=10,y=22)",px("slider_knob",10,22),"~#35D6C4"),
("display","fill",px("display",32,32),"#171A21"),("display","border (x=0,y=32)",px("display",0,32),"#2A2F3A"),("display","glow (56,6) over card",px("display",56,6,CD),blend((53,214,196),.10*(1-np.hypot(56.5-62,6.5-2)/14),CD))]
with open(sys.argv[2],"w") as f:
    f.write("| File | Point | My PNG | Board |\n|---|---|---|---|\n")
    for n,pt,(h,a),b in rows:
        f.write(f"| {n} | {pt} | {h}{'' if a>0.995 else ' a%.2f'%a} | {b} |\n")
print(open(sys.argv[2]).read());print("OK" if ok else "FAIL")
