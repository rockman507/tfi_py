import numpy as np
import functools
#import warnings
from scipy.misc import factorial as fac

from os.path import join
from os import listdir
from time import clock
from scipy.misc import toimage
import multiprocessing

def zernike_rad(m, n, rho):
    """
    Make radial Zernike polynomial on coordinate grid **rho**.

    @param [in] m Radial Zernike index
    @param [in] n Azimuthal Zernike index
    @param [in] rho Radial coordinate grid
    @return Radial polynomial with identical shape as **rho**
    """
    if (np.mod(n-m, 2) == 1):
        return rho*0.0

    wf = rho*0.0
    for k in range(int((n-m)/2+1)):
        wf += rho**(n-2.0*k) * (-1.0)**k * fac(n-k) / ( fac(k) * fac( (n+m)/2.0 - k ) * fac( (n-m)/2.0 - k ) )
    return wf

def zernike(m, n, rho, phi, norm=True):
    """
    Calculate Zernike mode (m,n) on grid **rho** and **phi**.

    **rho** and **phi** should be radial and azimuthal coordinate grids of identical shape, respectively.

    @param [in] m Radial Zernike index
    @param [in] n Azimuthal Zernike index
    @param [in] rho Radial coordinate grid
    @param [in] phi Azimuthal coordinate grid
    @param [in] norm Normalize modes to unit variance
    @return Zernike mode (m,n) with identical shape as rho, phi
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
    Convert linear Noll index to tuple of Zernike indices.

    j is the linear Noll coordinate, n is the radial Zernike index and m is the azimuthal Zernike index.

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
    """
    Calculate a basis of **nmodes** Zernike modes with radius **rad**.

    ((If **mask** is true, set everything outside of radius **rad** to zero (default). If this is not done, the set of Zernikes will be **rad** by **rad** square and are not orthogonal anymore.)) --> Nothing is masked, do this manually using the 'mask' entry in the returned dict.

    This output of this function can be used as cache for other functions.

    @param [in] nmodes Number of modes to generate
    @param [in] rad Radius of Zernike modes
    @param [in] modestart First mode to calculate (Noll index, i.e. 1=piston)
    @param [in] calc_covmat Return covariance matrix for Zernike modes, and its inverse
    @return Dict with entries 'modes' a list of Zernike modes, 'modesmat' a matrix of (nmodes, npixels), 'covmat' a covariance matrix for all these modes with 'covmat_in' its inverse, 'mask' is a binary mask to crop only the orthogonal part of the modes.
    """

    if (nmodes <= 0):
        return {'modes':[], 'modesmat':[], 'covmat':0, 'covmat_in':0, 'mask':[[0]]}
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
    if (calc_covmat):
        # Calculate covariance matrix
        covmat = np.array([[np.sum(zerni * zernj * grid_mask) for zerni in zern_modes] for zernj in zern_modes])
        # Invert covariance matrix using SVD
        covmat_in = np.linalg.pinv(covmat)

    # Create and return dict
    return {'modes': zern_modes, 'modesmat': zern_modes_mat, 'covmat':covmat, 'covmat_in':covmat_in, 'mask': grid_mask}

@profile
def fit_zernike(wavefront, zern_data={}, nmodes=10, startmode=1, fitweight=None, center=(-0.5, -0.5), rad=-0.5, rec_zern=True, err=None):
    """
    Fit **nmodes** Zernike modes to a **wavefront**.

    The **wavefront** will be fit to Zernike modes for a circle with radius **rad** with origin at **center**. **weigh** is a weighting mask used when fitting the modes.

    If **center** or **rad** are between 0 and -1, the values will be interpreted as fractions of the image shape.

    **startmode** indicates the Zernike mode (Noll index) to start fitting with, i.e. ***startmode**=4 will skip piston, tip and tilt modes. Modes below this one will be set to zero, which means that if **startmode** == **nmodes**, the returned vector will be all zeroes. This parameter is intended to ignore low order modes when fitting (piston, tip, tilt) as these can sometimes not be derived from data.

    If **err** is an empty list, it will be filled with measures for the fitting error:
    1. Mean squared difference
    2. Mean absolute difference
    3. Mean absolute difference squared

    This function uses **zern_data** as cache. If this is not given, it will be generated. See calc_zern_basis() for details.

    @param [in] wavefront Input wavefront to fit
    @param [in] zern_data Zernike basis cache
    @param [in] nmodes Number of modes to fit
    @param [in] startmode Start fitting at this mode (Noll index)
    @param [in] fitweight Mask to use as weights when fitting
    @param [in] center Center of Zernike modes to fit
    @param [in] rad Radius of Zernike modes to fit
    @param [in] rec_zern Reconstruct Zernike modes and calculate errors.
    @param [out] err Fitting errors
    @return Tuple of (wf_zern_vec, wf_zern_rec, fitdiff) where the first element is a vector of Zernike mode amplitudes, the second element is a full 2D Zernike reconstruction and the last element is the 2D difference between the input wavefront and the full reconstruction.
    @see See calc_zern_basis() for details on **zern_data** cache
    """

    if (rad < -1 or min(center) < -1):
        raise ValueError("illegal radius or center < -1")
    elif (rad > 0.5*max(wavefront.shape)):
        raise ValueError("radius exceeds wavefront shape?")
    elif (max(center) > max(wavefront.shape)-rad):
        raise ValueError("fitmask shape exceeds wavefront shape?")
    elif (startmode	< 1):
        raise ValueError("startmode<1 is not a valid Noll index")

    # Convert rad and center if coordinates are fractional
    if (rad < 0):
        rad = -rad * min(wavefront.shape)
    if (min(center) < 0):
        center = -np.r_[center] * min(wavefront.shape)

    # Make cropping slices to select only central part of the wavefront
    xslice = slice(center[0]-rad, center[0]+rad)
    yslice = slice(center[1]-rad, center[1]+rad)

    # Compute Zernike basis if absent
    #if (not zern_data.has_key('modes')):
    if 'modes' not in zern_data:
        tmp_zern = calc_zern_basis(nmodes, rad)
        zern_data['modes'] = tmp_zern['modes']
        zern_data['modesmat'] = tmp_zern['modesmat']
        zern_data['covmat'] = tmp_zern['covmat']
        zern_data['covmat_in'] = tmp_zern['covmat_in']
        zern_data['mask'] = tmp_zern['mask']
    # Compute Zernike basis if insufficient
    elif (nmodes > len(zern_data['modes']) or
        zern_data['modes'][0].shape != (2*rad, 2*rad)):
        tmp_zern = calc_zern_basis(nmodes, rad)
        # This data already exists, overwrite it with new data
        zern_data['modes'] = tmp_zern['modes']
        zern_data['modesmat'] = tmp_zern['modesmat']
        zern_data['covmat'] = tmp_zern['covmat']
        zern_data['covmat_in'] = tmp_zern['covmat_in']
        zern_data['mask'] = tmp_zern['mask']

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
        #wf_zern_vec = np.dot(wf_w, np.linalg.pinv(zern_basismat[:, grid_vec] * weight)).ravel()
        # This is 5x faster:
        wf_zern_vec = np.linalg.lstsq((zern_basismat[:, grid_vec] * weight).T, wf_w.ravel())[0]
    else:
        # LSQ fit with data. Only fit inside grid_mask

        # Crop out central region of wavefront, then only select the orthogonal part of the Zernike modes (grid_mask)
        wf_w = ((wavefront[yslice, xslice])[grid_mask]).reshape(1,-1)
        #wf_zern_vec = np.dot(wf_w, np.linalg.pinv(zern_basismat[:, grid_vec])).ravel()
        # This is 5x faster
        wf_zern_vec = np.linalg.lstsq(zern_basismat[:, grid_vec].T, wf_w.ravel())[0]

    wf_zern_vec[:startmode-1] = 0

    # Calculate full Zernike phase & fitting error
    if (rec_zern):
        wf_zern_rec = calc_zernike(wf_zern_vec, zern_data=zern_data, rad=min(wavefront.shape)/2)
        fitdiff = (wf_zern_rec - wavefront[yslice, xslice])
        fitdiff[grid_mask == False] = fitdiff[grid_mask].mean()
    else:
        wf_zern_rec = None
        fitdiff = None

    if (err != None):
        # For calculating scalar fitting qualities, only use the area inside the mask
        fitresid = fitdiff[grid_mask == True]
        err.append((fitresid**2.0).mean())
        err.append(np.abs(fitresid).mean())
        err.append(np.abs(fitresid).mean()**2.0)

    return (wf_zern_vec, wf_zern_rec, fitdiff)

def calc_zernike(zern_vec, rad, zern_data={}, mask=True):
    """
    Construct wavefront with Zernike amplitudes **zern_vec**.

    Given vector **zern_vec** with the amplitude of Zernike modes, return the reconstructed wavefront with radius **rad**.

    This function uses **zern_data** as cache. If this is not given, it will be generated. See calc_zern_basis() for details.

    If **mask** is True, set everything outside radius **rad** to zero, this is the default and will use orthogonal Zernikes. If this is False, the modes will not be cropped.

    @param [in] zern_vec 1D vector of Zernike amplitudes
    @param [in] rad Radius for Zernike modes to construct
    @param [in] zern_data Zernike basis cache
    @param [in] mask If True, set everything outside the Zernike aperture to zero, otherwise leave as is.
    @see See calc_zern_basis() for details on **zern_data** cache and **mask**
    """
    # Compute Zernike basis if absent
    #if (not zern_data.has_key('modes')):
    if 'modes' not in zern_data:
        tmp_zern = calc_zern_basis(len(zern_vec), rad)
        zern_data['modes'] = tmp_zern['modes']
        zern_data['modesmat'] = tmp_zern['modesmat']
        zern_data['covmat'] = tmp_zern['covmat']
        zern_data['covmat_in'] = tmp_zern['covmat_in']
        zern_data['mask'] = tmp_zern['mask']
    # Compute Zernike basis if insufficient
    elif (len(zern_vec) > len(zern_data['modes'])):
        tmp_zern = calc_zern_basis(len(zern_vec), rad)
        # This data already exists, overwrite it with new data
        zern_data['modes'] = tmp_zern['modes']
        zern_data['modesmat'] = tmp_zern['modesmat']
        zern_data['covmat'] = tmp_zern['covmat']
        zern_data['covmat_in'] = tmp_zern['covmat_in']
        zern_data['mask'] = tmp_zern['mask']
    zern_basis = zern_data['modes']

    gridmask = 1
    if (mask):
        gridmask = zern_data['mask']

    # Reconstruct the wavefront by summing modes
    return functools.reduce(lambda x,y: x+y[1]*zern_basis[y[0]] * gridmask, enumerate(zern_vec), 0)


def get_zernike(args):
    filename = args[0]
    path = args[1]
    path_raw = args[2]
    path_images = args[3]
    mask = args[4]
    size = args[5]
    modes = args[6]
    nan = np.NaN

    # Setup output filenames
    zz = clock()
    unwrapped_file = join(path_raw, filename)
    zernike_file = join(path_raw, 'zernike_'+filename[10:15]+'.dat')
    image_file = join(path_images, 'zernike_'+filename[10:15]+'.bmp')
    diff_image_file = join(path_images, 'zernike_diff_'+filename[10:15]+'.bmp')

    # Get array
    if modes == 0:
        modes = 15
    unwrapped_file1 = open(unwrapped_file, 'rb')
    arr = np.fromfile(unwrapped_file, dtype='f')
    arr.resize(size)
    mask = ~mask

    # Calc zernike fit and apply mask
    err = []
    cache = {}
    fitvec, fitrec, fitdiff = fit_zernike(arr, nmodes=modes, err=err)
    #fitvec, fitrec, fitdiff = fit_zernike(arr, nmodes=modes, err=err)
    #fitvec, fitrec, fitdiff = fit_zernike(arr, nmodes=modes, err=err, zern_data=cache)
    #fitvec, fitrec, fitdiff = fit_zernike(arr, nmodes=modes, err=err, zern_data=cache)
    
    fitdiff = np.array(fitdiff, dtype='f')
    fitdiff[mask] = 0
    fitrec = np.array(fitrec, dtype='f')
    fitrec[mask] = 0

    # Save image files
    fitdiff.tofile(zernike_file)
    toimage(fitrec).save(image_file)
    toimage(fitdiff).save(diff_image_file)

    try:
        piston = fitvec[0]
    except:
        piston = nan
    try:
        tilt = np.sqrt(fitvec[1]**2+fitvec[2]**2)
    except:
        tilt = nan
    try:
        astig = np.sqrt(fitvec[4]**2+fitvec[5]**2)
    except:
        astig = nan
    try:
        power = fitvec[3]
    except:
        power = nan
    try:
        sphere = fitvec[10]
    except:
        sphere = nan

    print(filename)
    return '{},{:f},{:f},{:f},{:f},{:f},{:f},{:f},{:f}\n'.format(filename,
        piston, tilt, astig, power, sphere, err[0], err[1], err[2])


if __name__ == '__main__':
    # Get path
    tmpz = clock()
    #path = diropenbox('Pick directory to process',default=r'd:\phase')
    #path = win32api.GetShortPathName(path)
    #print path
    path = r'C:\DOCUME~1\jsaredy\Desktop\41_201~1'
    path_raw = join(path, r'raw')
    path_images = join(path, r'images')

    # Get mask and array size
    mask_path = join(path, r'mask.dat')
    mask_file = open(mask_path, 'rb')
    mask = np.fromfile(mask_file, dtype='bool')
    tmp = np.sqrt(mask.shape)[0]
    arr_size = tmp, tmp
    mask.resize(arr_size)
    #toimage(mask).show()

    # Get unwrapped arrays
    raw_filenames = listdir(path_raw)

    for raw_filename in raw_filenames[:]:
        if 'unwrapped_.dat' != raw_filename[:10]+raw_filename[15:]:
            raw_filenames.remove(raw_filename)

    temp = 'piston, tilt, astrig, power, sphere\n'
    print(str(clock()-tmpz))
    zz = clock()
    A = []
    summary = ''

    for filename in raw_filenames:
        A.append((filename, path, path_raw, path_images, mask, arr_size, 50))

    get_zernike(A[0])
    #mapi = map(get_zernike, A)

    #for x in mapi:
    #    summary += x
    #    print(x)

    print(str(clock()-zz))
    print(summary)


