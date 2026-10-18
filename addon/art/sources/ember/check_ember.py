import sys,os,numpy as np
from PIL import Image
d=sys.argv[1]
L=lambda n:np.asarray(Image.open(f"{d}/ember_{n}.png").convert("RGBA"),float)
exp={"frame":(128,128),"panel":(256,256),"heat":(128,16),"rivet":(16,16),"plate":(64,64),"display":(64,64),"slot_normal":(64,64),"slot_hover":(64,64),"slot_on":(64,64),"btn_normal":(128,32),"btn_hover":(128,32),"btn_primary":(128,32),"btn_primary_hover":(128,32),"btn_disabled":(128,32),"check_off":(32,32),"check_on":(32,32),"switch_off":(64,32),"switch_on":(64,32),"switch_knob_off":(32,32),"switch_knob_on":(32,32),"slider_track":(128,16),"slider_fill":(128,16),"slider_knob":(32,32),"rule":(64,8)}
ok=True
for n,(w,h) in exp.items():
    a=L(n)
    if a.shape[:2]!=(h,w): print("SIZE",n,a.shape);ok=False
    # edge clipping (alpha on border) for glow pieces
    if n in("slider_knob","switch_knob_on","check_on","slot_on") :
        b=max(a[0,:,3].max(),a[-1,:,3].max(),a[:,0,3].max(),a[:,-1,3].max())
        if n!="slot_on" and b>8: print("EDGE",n,b);ok=False
p=L("panel");print("panel seam",abs(p[0]-p[-1]).mean(),abs(p[:,0]-p[:,4]).mean(),"vs",abs(p[0]-p[1]).mean())
def plain(n,axis,lo,hi):
    a=L(n);s=a[:,lo:hi] if axis=="x" else a[lo:hi]
    m=abs(s-s[:,:1]).max() if axis=="x" else abs(s-s[:1]).max()
    print("plain",n,axis,m)
    return m<1.5
for n in["btn_normal","btn_hover","btn_primary","btn_primary_hover","btn_disabled"]:ok&=plain(n,"x",16,112)
for n in["plate","display","slot_normal","slot_hover","slot_on"]:ok&=plain(n,"x",16,48)&plain(n,"y",16,48)
ok&=plain("frame","x",32,96)&plain("frame","y",32,96)
ok&=plain("heat","x",0,128)
ok&=plain("slider_track","x",8,120)
for n in["frame","panel"]:pass
k0,k1=L("switch_knob_off")[...,3],L("switch_knob_on")[...,3]
print("knob core same",abs((k0>250)^(k1>250)).sum())
def hx(n,x,y):
    a=L(n)[y,x];return "#%02X%02X%02X a%.2f"%(*[int(v) for v in a[:3]],a[3]/255)
for n,x,y,b in[("btn_normal",64,8,"#4d4a46→ ~#403d39"),("btn_normal",64,26,"~#2d2b29"),("btn_primary",64,2,"#ffd36a"),("btn_primary",64,28,"~#c4480c"),("slot_normal",32,10,"~#363330"),("slot_on",1,32,"#FF7A2E"),("plate",32,32,"#161412"),("slider_fill",2,8,"#c4480c"),("slider_fill",125,8,"#ffc247"),("frame",1,64,"#0c0b0a"),("frame",4,64,"#57524c")]:
    print(n,(x,y),hx(n,x,y),"board",b)
print("OK" if ok else "FAIL")
