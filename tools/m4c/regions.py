"""Camera-independent object-space anatomical fields, editable in regions.json.

These are proposed surface regions, not medical claims or new muscle geometry.
"""
import numpy as np
from scipy.interpolate import CubicSpline
from matplotlib.path import Path as Polygon

class Regions:
    def __init__(self, specification, front_visible=None):
        self.front_visible=front_visible
        self.spec=specification;self.d=specification['landmarks']['deltoid']
        p=np.array(specification['landmarks']['pectoralContourXY']);p=np.r_[p,p[:1]]
        t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
        curve=CubicSpline(t,p,bc_type='periodic')(np.linspace(0,t[-1],400,endpoint=False))
        self.pec=Polygon(curve)
    def classify(self, points, normals):
        x,y,z=points.T;sx=np.abs(x);nz=normals[:,2]
        ids=np.zeros(len(points),np.uint8)
        pectoral=self.pec.contains_points(np.column_stack([sx,y]))&(z>.024)&(nz>0)
        if self.front_visible is not None:
            axillary=(sx>.135)&(y<.545)
            pectoral &= self.front_visible(points) & (~axillary | self.front_visible(points,.0015))
        ids[pectoral]=np.where(x[pectoral]>0,1,2)
        d=self.d;t=np.clip((y-d['insertionY'])/(d['topY']-d['insertionY']),0,1)
        inner=d['innerXBottom']+(d['innerXTop']-d['innerXBottom'])*t**.82
        phi=np.arctan2(z-d['axisZ'],sx-d['axisX'])
        bottom=d['insertionY']+.105*(np.clip(np.abs(phi)/1.7,0,1)**1.25)
        top=d['topY']-.018*np.clip(np.abs(phi)/1.8,0,1)**1.4
        outward=normals[:,0]*np.where(x>=0,1,-1)
        cap=(sx>inner)&(y>bottom)&(y<top)&(np.abs(phi)<2.05)&(outward>-.28)
        # Three origins spread over the upper cap and converge at the insertion.
        anterior=d['insertionZ']+(d['anteriorOriginZ']-d['insertionZ'])*t**.85+.007*np.sin(np.pi*t)
        # The medial/clavicular origin belongs to the anterior fan, while
        # the lateral fan remains on the outer dome. Smooth 3D transition.
        medial=np.clip((.18-sx)/.025,0,1);medial=medial*medial*(3-2*medial)
        upper=np.clip((y-.60)/.03,0,1);upper=upper*upper*(3-2*upper)
        anterior-=.028*medial*upper
        posterior=d['insertionZ']+(d['posteriorOriginZ']-d['insertionZ'])*t**.85-.007*np.sin(np.pi*t)
        portion=np.where(z>anterior,0,np.where(z<posterior,2,1))
        ids[cap]=(3+portion[cap]+np.where(x[cap]>0,0,3)).astype(np.uint8)
        return ids
