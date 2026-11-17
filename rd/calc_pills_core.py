import math
def vol(shape,L,W,t):
    if shape=="capsule": r=W/2; return math.pi*r*r*(L-2*r)+4/3*math.pi*r**3
    if shape=="round": return math.pi/4*L*L*t*0.85
    return math.pi/4*L*W*t*0.85
# openings (mm) from the v0.9 CAD
R_O,R_I,N=47.0,23.0,15
def comp_fits(L,W,t):
    # try orientations: (radial, tangential, axial)
    for a,b,c in [(L,W,t),(L,t,W),(W,L,t),(W,t,L),(t,L,W),(t,W,L)]:
        if a>24 or c>13: continue
        r_in=R_O-a
        w=min(2*math.pi*r_in/N-1.0, 14.8)
        if b<=w: return True
    return False
def passes(s, A, B):  # pill sorted dims s1<=s2<=s3 through rectangle A x B
    a,b=sorted((A,B)); return s[0]<=a and s[1]<=b
