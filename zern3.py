import numpy as np
import functools
#import warnings
from scipy.misc import factorial as fac
import time

def zernike_rad(m, n, rho):
    if (np.mod(n-m, 2) == 1):
        return rho*0.0
    wf = rho*0.0
    for k in range(int((n-m)/2+1)):
        wf += rho**(n-2.0*k) * (-1.0)**k * fac(n-k) / ( fac(k) * fac( (n+m)/2.0 - k ) * fac( (n-m)/2.0 - k ) )
    return wf

def zernike(m, n, rho, phi, norm=True):
    """
    @see <http://research.opt.indiana.edu/Library/VSIA/VSIA-2000_taskforce/TOPS4_2.html> and <http://research.opt.indiana.edu/Library/HVO/Handbook.html>.
    """
    nc = 1.0
    if (norm):
        nc = (2*(n+1)/(1+(m==0)))**0.5
    if (m > 0): return nc*zernike_rad(m, n, rho) * np.cos(m * phi)
    if (m < 0): return nc*zernike_rad(-m, n, rho) * np.sin(-m * phi)
    return nc*zernike_rad(0, n, rho)

def noll_to_zern(j):
    """
    @param [in] j Zernike mode Noll index
    @return (n, m) tuple of Zernike indices
    @see <https://oeis.org/A176988>.
    """
    if (j == 0):
        raise ValueError("Noll indices start at 1, 0 is invalid.")

    n = 0
    j1 = j-1
    while (j1 > n):
        n += 1
        j1 -= n

    m = (-1)**j * ((n % 2) + 2 * int((j1+((n+1)%2)) / 2.0 ))
    #print(n,m)
    return (n, m)

def zernikel(j, rho, phi, norm=True):
    n, m = noll_to_zern(j)
    return zernike(m, n, rho, phi, norm)

def mk_rad_mask(r0, r1=None, norm=True, center=None, dtype=np.float):
    """
    Make a rectangular matrix of size (r0, r1) where the value of each 
    element is the Euclidean distance to **center**. If **center** is not 
    given, it is the middle of the matrix. If **norm** is True (default), 
    the distance is normalized to half the radius, i.e. values will range 
    from [-1, 1] for both axes.

    If only r0 is given, the matrix will be (r0, r0). If r1 is also given, 
    the matrix will be (r0, r1)

    To make a circular binary mask of (r0, r0), use
        mk_rad_mask(r0) < 1

    @param [in] r0 The width (and height if r1==None) of the mask.
    @param [in] r1 The height of the mask.
    @param [in] norm Normalize the distance such that 2/(r0, r1) equals a distance of 1.
    @param [in] center Set distance origin to **center** (defaults to the middle of the rectangle)
    """

    if (not r1):
        r1 = r0
    if (r0 < 0 or r1 < 0):
        #warnings.warn("mk_rad_mask(): r0 < 0 or r1 < 0?")
        print("mk_rad_mask(): r0 < 0 or r1 < 0?")
    
    if (center != None and norm and sum(center)/len(center) > 1):
        raise ValueError("|center| should be < 1 if norm is set")	

    if (center == None):
        if (norm): center = (0, 0)
        else: center = (r0/2.0, r1/2.0)

    # N.B. These are calculated separately because we cannot calculate  
    # 2.0/r0 first and multiply r0v with it depending on **norm**, this will 
    # yield different results due to rounding errors.
    if (norm):
        r0v = np.linspace(-1-center[0], 1-center[0], r0).astype(dtype).reshape(-1,1)
        r1v = np.linspace(-1-center[1], 1-center[1], r1).astype(dtype).reshape(1,-1)
    else:
        r0v = np.linspace(0-center[0], r0-center[0], r0).astype(dtype).reshape(-1,1)
        r1v = np.linspace(0-center[1], r1-center[1], r1).astype(dtype).reshape(1,-1)
    
    return (r0v**2. + r1v**2.)**0.5

def calc_zern_basis(nmodes, rad, modestart=1, calc_covmat=False):

    if (nmodes <= 0):
        return {'modes':[], 'modesmat':[], 'mask':[[0]]}
    if (rad <= 0):
        raise ValueError("radius should be > 0")
    if (modestart <= 0):
        raise ValueError("**modestart** Noll index should be > 0")

    # Use vectors instead of a grid matrix
    rvec = ((np.arange(2.0*rad) - rad)/rad)
    r0 = rvec.reshape(-1,1)
    r1 = rvec.reshape(1,-1)
    grid_rad = mk_rad_mask(2*rad)
    grid_ang = np.arctan2(r0, r1)

    grid_mask = grid_rad <= 1

    # Build list of Zernike modes, these are *not* masked/cropped
    zern_modes = [zernikel(zmode, grid_rad, grid_ang) for zmode in range(modestart, nmodes+modestart)]

    # Convert modes to (nmodes, npixels) matrix
    zern_modes_mat = np.r_[zern_modes].reshape(nmodes, -1)

    covmat = covmat_in = None

    # Create and return dict
    return {'modes': zern_modes, 'modesmat': zern_modes_mat, 'mask': grid_mask}


def fit_zernike(wavefront, zern_data={}, nmodes=10, startmode=1, fitweight=None, center=(-0.5, -0.5), rad=-0.5, rec_zern=True):
    zern_data = {}
    # Convert rad and center if coordinates are fractional
    rad = -rad * min(wavefront.shape)
    center = -np.r_[center] * min(wavefront.shape)

    # Make cropping slices to select only central part of the wavefront
    xslice = slice(center[0]-rad, center[0]+rad)
    yslice = slice(center[1]-rad, center[1]+rad)

    # Compute Zernike basis if absent
    if 'modes' not in zern_data:
        tmp_zern = calc_zern_basis(nmodes, rad)
        zern_data['modes'] = tmp_zern['modes']
        zern_data['modesmat'] = tmp_zern['modesmat']
        zern_data['mask'] = tmp_zern['mask']
    # Compute Zernike basis if insufficient


    zern_basis = zern_data['modes'][:nmodes]
    zern_basismat = zern_data['modesmat'][:nmodes]
    grid_mask = zern_data['mask']

    wf_zern_vec = 0
    grid_vec = grid_mask.reshape(-1)
    if (fitweight != None):
        # Weighed LSQ fit with data. Only fit inside grid_mask

        # Multiply weight with binary mask, reshape to vector
        weight = ((fitweight[yslice, xslice])[grid_mask]).reshape(1,-1)

        # LSQ fit with weighed data
        wf_w = ((wavefront[yslice, xslice])[grid_mask]).reshape(1,-1) * weight
        wf_zern_vec = np.linalg.lstsq((zern_basismat[:, grid_vec] * weight).T, wf_w.ravel())[0]
    else:
        # LSQ fit with data. Only fit inside grid_mask
        
        # Crop out central region of wavefront, then only select the orthogonal part of the Zernike modes (grid_mask)
        wf_w = ((wavefront[yslice, xslice])[grid_mask]).reshape(1,-1)
        wf_zern_vec = np.linalg.lstsq(zern_basismat[:, grid_vec].T, wf_w.ravel())[0]

    wf_zern_vec[:startmode-1] = 0

    # Calculate full Zernike phase & fitting error
    if (rec_zern):
        wf_zern_rec = calc_zernike(wf_zern_vec, zern_data=zern_data, rad=min(wavefront.shape)/2)
        fitdiff = (wf_zern_rec - wavefront[yslice, xslice])
        fitdiff[grid_mask == False] = fitdiff[grid_mask].mean()

    # For calculating scalar fitting qualities, only use the area inside the mask
    fitresid = fitdiff[grid_mask == True]
    
    err = []
    err.append((fitresid**2.0).mean())
    err.append(np.abs(fitresid).mean())
    err.append(np.abs(fitresid).mean()**2.0)
    
    return (wf_zern_vec, wf_zern_rec, fitdiff, err)

def calc_zernike(zern_vec, rad, zern_data={}, mask=True):
    zern_basis = zern_data['modes']

    gridmask = 1
    if (mask):
        gridmask = zern_data['mask']

    # Reconstruct the wavefront by summing modes
    return functools.reduce(lambda x,y: x+y[1]*zern_basis[y[0]] * gridmask, enumerate(zern_vec), 0)



