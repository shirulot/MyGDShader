"""只读检查资源对实验有用的性质；不生成或修改PNG。"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]

def main():
    catalog=json.loads((HERE/'catalog.json').read_text(encoding='utf-8'))
    checks=[]; images={}
    def check(name,passed): checks.append(dict(check=name,pass_=bool(passed)))
    for a in catalog['assets']:
        p=ROOT/a['file'].removeprefix('res://'); im=Image.open(p)
        check(a['id']+' sha',hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256'])
        check(a['id']+' canvas/mode',list(im.size)==a['canvas'] and im.mode==a['mode'])
        images[a['id']]=np.array(im)
    check('gray 256 exact values',np.array_equal(images['grayscale_gradient'][0,:,0],np.arange(256)))
    check('color Ramp endpoints',images['color_ramp'][0,0].tolist()==[16,24,32] and images['color_ramp'][0,-1].tolist()==[255]*3)
    check('circle solid/empty/soft',images['circle_mask'][128,128]==255 and images['circle_mask'][0,0]==0 and len(np.unique(images['circle_mask']))>2)
    check('star binary and meaningful',set(np.unique(images['star_mask']))=={0,255} and 1000<np.count_nonzero(images['star_mask'])<30000)
    spectral={}
    for name in ('noise_low','noise_high'):
        a=images[name].astype(float)
        check(name+' XY endpoints',np.array_equal(a[0],a[-1]) and np.array_equal(a[:,0],a[:,-1]))
        check(name+' endpoint first difference',np.array_equal(a[1]-a[0],a[-1]-a[-2]) and np.array_equal(a[:,1]-a[:,0],a[:,-1]-a[:,-2]))
        check(name+' valid contrast',a.std()>20 and a.min()==0 and a.max()==255)
        power=np.abs(np.fft.fft2(a-a.mean()))**2
        fx,fy=np.meshgrid(np.fft.fftfreq(256)*256,np.fft.fftfreq(256)*256)
        spectral[name]=float((power*np.hypot(fx,fy)).sum()/power.sum())
    check('high spatial frequency distinct',spectral['noise_high']>spectral['noise_low']*2)
    a=images['alpha_edge_test'][...,3]
    check('alpha interior hole',a[46,46]==0 and a[22,22]==255)
    check('alpha dedicated thin lines',a[52,100]==255 and a[51,100]==0 and a[53,100]==0)
    check('alpha partial gradients',len(np.unique(a))>30 and a[112,12]==0 and a[112,75]==255)
    check('radial endpoints',images['radial_ramp'][128,128]>250 and images['radial_ramp'][0,0]==0)
    stripe=images['energy_stripe']
    check('stripe32 period',np.array_equal(stripe[:,:224],stripe[:,32:]))
    h=images['test_height']; n=images['test_normal']
    check('known convex/concave',h[46,35]>170 and h[46,91]<85)
    check('OpenGL X ramp points left',n[98,30,0]<128 and n[98,30,1]==128)
    check('OpenGL Y ramp points up',n[100,94,1]>128 and n[100,94,0]==128)
    vectors=n.astype(float)/255*2-1
    check('encoded normal unit hemisphere',np.max(np.abs(np.linalg.norm(vectors,axis=2)-1))<.012 and n[...,2].min()>127)
    for name in ('rain_line','water_drop','spark','dust_dot'):
        a=images[name][...,3]; check(name+' alpha/coverage',set(np.unique(a))=={0,255} and 1<np.count_nonzero(a)<100)
    failures=[c['check'] for c in checks if not c['pass_']]
    result=dict(status='BASIC_20_NUMERIC_PASS' if not failures else 'BASIC_20_FAILED',checks=len(checks),failed_checks=len(failures),
        failures=failures,spectral_centroid_cycles_per_image=spectral,results=checks,
        asset_sha256={a['id']:a['sha256'] for a in catalog['assets']})
    (HERE/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('results','asset_sha256')}))
    if failures: raise SystemExit(1)

if __name__=='__main__': main()
