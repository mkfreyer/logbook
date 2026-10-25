"""Transport only the existing depression field, using the user's two open paths.

The intermediate camera-depth grid is a numerical authoring tool. It is never
used as a texture, normal map, material input or painted line in the asset.
Final coordinates change in the actual deltoid mesh; all vertex/face IDs remain.
"""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from scipy.interpolate import PchipInterpolator

p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();data=np.load(a.source);v=data['v'];f=data['f'];basis=data['basis'];origin=data['cam']
c=(v-origin)@basis;uv=np.c_[480+c[:,0]*2400,432-c[:,1]*2400];H,W=864,960

def sample(grid,xy):
    return ndi.map_coordinates(grid,np.array([xy[...,1].ravel(),xy[...,0].ravel()]),order=1,mode='nearest').reshape(xy.shape[:-1])

def smooth(t):
    t=np.clip(t,0,1);return t*t*(3-2*t)

front=np.full((H,W),-np.inf);back=np.full((H,W),np.inf)
for tri in f:
    t=uv[tri];z=c[tri,2];x0=max(0,int(np.floor(t[:,0].min())));x1=min(W-1,int(np.ceil(t[:,0].max())))
    y0=max(0,int(np.floor(t[:,1].min())));y1=min(H-1,int(np.ceil(t[:,1].max())))
    if x0>x1 or y0>y1:continue
    xx,yy=np.meshgrid(np.arange(x0,x1+1),np.arange(y0,y1+1))
    den=(t[1,1]-t[2,1])*(t[0,0]-t[2,0])+(t[2,0]-t[1,0])*(t[0,1]-t[2,1])
    if abs(den)<1e-8:continue
    aa=((t[1,1]-t[2,1])*(xx-t[2,0])+(t[2,0]-t[1,0])*(yy-t[2,1]))/den
    bb=((t[2,1]-t[0,1])*(xx-t[2,0])+(t[0,0]-t[2,0])*(yy-t[2,1]))/den
    keep=(aa>=-1e-6)&(bb>=-1e-6)&(aa+bb<=1+1e-6);zz=aa*z[0]+bb*z[1]+(1-aa-bb)*z[2]
    np.maximum(front[y0:y1+1,x0:x1+1],np.where(keep,zz,-np.inf),out=front[y0:y1+1,x0:x1+1])
    np.minimum(back[y0:y1+1,x0:x1+1],np.where(keep,zz,np.inf),out=back[y0:y1+1,x0:x1+1])
valid=np.isfinite(front);nearest=ndi.distance_transform_edt(~valid,return_distances=False,return_indices=True)
front=front[tuple(nearest)];back=np.where(np.isfinite(back),back,front)
edge=ndi.distance_transform_edt(valid)
foot=np.mgrid[-40:41,-40:41];foot=(foot**2).sum(0)<=40**2
envelope=ndi.grey_closing(front,footprint=foot)
depression=np.maximum(0,envelope-front)
# Hand-traced open paths from the supplied 320x384 annotation. Green outlines
# are deliberately not input: they identify reliefs, not new anatomical shapes.
red1=np.array([[92,130],[80,153],[69,180],[60,208],[54,230],[53,258],[53,286],[57,300],[65,319],[78,335],[94,350]],float)
blue1=np.array([[55,292],[57,312],[57,333],[60,353],[64,370],[70,378]],float)
red2=np.array([[230,82],[233,100],[234,128],[231,160],[225,192],[217,223],[207,254],[194,286],[179,315],[161,344]],float)
blue2=np.array([[229,72],[230,90],[219,123],[213,151],[207,185],[200,217],[187,251],[174,280],[164,315],[149,352],[132,379]],float)
# Corresponding original valleys, localized on the actual P4 camera projection.
# The image is a cropped reference, so transfer the relative red-to-blue motion
# from corresponding surface landmarks, rather than assuming a full-frame origin.
old1=np.array([[348,285],[328,325],[312,375],[301,425],[305,475],[320,511],[340,545],[362,566]],float)
old2=np.array([[567,218],[550,275],[546,325],[529,375],[518,400],[443,425],[450,450],[453,475],[470,525],[461,550]],float)
yy,xx=np.indices((H,W));grid=np.stack([xx,yy],axis=-1).astype(float)
curves=[];all_removed=np.zeros((H,W));all_new=np.zeros((H,W));descriptions=[]
for index,(red,blue,old)in enumerate([(red1,blue1,old1),(red2,blue2,old2)]):
    xold=PchipInterpolator(old[:,1],old[:,0],extrapolate=False)
    sy=np.linspace(old[0,1],old[-1,1],300);sx=ndi.gaussian_filter1d(xold(sy),4.)
    if index==0:
        # The upper part is intentionally unchanged. Only the lower turn moves.
        t=np.clip((sy-490)/(old[-1,1]-490),0,1)
        ry=292+t*(350-292);by=292+t*(378-292)
        rx=np.interp(ry,red[:,1],red[:,0]);bx=np.interp(by,blue[:,1],blue[:,0])
        dx=1.25*(bx-rx)*smooth((sy-483)/20);dy=1.25*(by-ry)*smooth((sy-483)/20)
    else:
        t=(sy-old[0,1])/(old[-1,1]-old[0,1])
        ry=82+t*(344-82);by=72+t*(379-72)
        rx=np.interp(ry,red[:,1],red[:,0]);bx=np.interp(by,blue[:,1],blue[:,0])
        dx=1.25*(bx-rx)*smooth(t/.10);dy=1.25*(by-ry)*smooth(t/.10)
    new=np.c_[sx+dx,sy+dy];curves.append((np.c_[sx,sy],new))
    # Compact corridor around each OLD trough, C2 fade at its ends and banks.
    safe_y=np.clip(yy,sy[0],sy[-1]);center=np.interp(safe_y,sy,sx)
    fade=smooth((yy-sy[0]+10)/28)*smooth((sy[-1]+24-yy)/30)
    corridor=smooth((35-np.abs(xx-center))/13)*fade
    # Exclude surface rims, backing mesh and clinically unrelated deep contacts.
    guard=smooth((edge-4)/8)*smooth(((front-back)-.005)/.008)
    lower_only=smooth((yy-483)/30) if index==0 else np.ones_like(front)
    removed=np.minimum(depression,.004)*corridor*guard*lower_only
    removed=ndi.gaussian_filter(removed,(1.2,.7))
    # Pull-back of the relief field through a smooth invertible 2D displacement.
    def displacement(xy):
        y=xy[...,1];clipy=np.clip(y,sy[0],sy[-1]);center=np.interp(clipy,sy,sx)
        wx=smooth((74-np.abs(xy[...,0]-center))/48)
        wy=smooth((y-sy[0]+35)/45)*smooth((sy[-1]+60-y)/65)
        return np.stack([np.interp(clipy,sy,dx),np.interp(clipy,sy,dy)],-1)*(wx*wy)[...,None]
    source=grid.copy()
    for _ in range(50):source=grid-displacement(source)
    transported=ndi.gaussian_filter(sample(removed,source),(3.,1.5))
    newx=np.interp(yy,new[:,1],new[:,0]);distance=np.abs(xx-newx)
    newfade=smooth((yy-new[0,1]-3)/28)*smooth((new[-1,1]+15-yy)/32)
    # Broad rounded extra depth, not a sharp slit. No outward bank inflation.
    floor=.0020*np.exp(-.5*(distance/10.)**2)*newfade*guard*lower_only
    requested=np.maximum(1.20*transported,floor)
    all_removed+=removed;all_new+=requested
    descriptions.append({'path':index+1,'reference_red_px':red.tolist(),'reference_blue_px':blue.tolist(),
        'old_surface_path_px':np.c_[sx,sy][::20].tolist(),'new_surface_path_px':new[::20].tolist(),
        'old_end_px':old[-1].tolist(),'new_end_px':new[-1].tolist(),
        'upper_first_path_preserved_until_original_y_px':490 if index==0 else None})

depth_delta=all_removed-all_new
# Local fairing regularizes old voxel/decimation facets inside these corridors.
roi=np.clip((all_removed+all_new)/.00015,0,1)
delta=sample(depth_delta,uv)
front_distance=np.abs(c[:,2]-sample(front,uv))
visible=1-smooth((front_distance-.0003)/.0010)
delta*=visible
# A complete fade at the outer silhouette prevents thickening of the cap rim.
delta*=sample(smooth((edge-3)/7),uv)
q=v+delta[:,None]*basis[:,2]
np.savez_compressed(a.output,v=q,f=f,source_v=v,delta_m=delta,affected=np.abs(delta)>1e-9)
def volume(v):return float(np.einsum('ij,ij->i',v[f[:,0]],np.cross(v[f[:,1]],v[f[:,2]])).sum()/6)
meta={'method':'Transport of existing local depression depth onto the two blue trajectories; true mesh displacement only.',
    'baseline_commit':'0ab3d838c728a88f2d325edff7a6884400c9ed78','paths':descriptions,
    'camera':'P4P5_epaule-droite','reference_size_px':[320,384],
    'registration':'Manual correspondence of existing valley landmarks in the same -55 degree view; relative annotation displacements scaled 1.25 to original render pixels. Not an automated pixel registration.',
    'pixels_per_meter':2400,'closing_radius_px':40,'rounded_extra_depth_m':.002,
    'new_textures_or_material_lines':False,'global_volume_compensation':False,
    'changed_vertices':int(np.count_nonzero(np.abs(delta)>1e-9)),
    'max_fill_m':float(delta.max()),'max_recession_m':float(-delta.min()),
    'volume_ratio':volume(q)/volume(v),'bbox_before_m':np.ptp(v,axis=0).tolist(),'bbox_after_m':np.ptp(q,axis=0).tolist(),
    'surface_builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
a.output.with_suffix('.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print('SURFACE',json.dumps({k:meta[k]for k in ['changed_vertices','max_fill_m','max_recession_m','volume_ratio','bbox_before_m','bbox_after_m']}))
