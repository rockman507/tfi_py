import numpy as np
from h5py import File
import os, re


#@profile
def get_mask(path, border=0, size=True):

    #Get mask shape
    f = File(path, 'r')
    sub = f.get(r'measurement0/maskshapes/Detector')
    sub2 = f.get(r'measurement0/frames/frame_full/data')
    X,Y = sub2.shape
    X -= 2
    Y -= 2
    temp = sub.attrs.get('shape1')
    temp = re.split('[| ,]', temp)
    f.close()

    left = int(float(temp[1]))
    top = int(float(temp[3]))
    width = int(float(temp[5]))
    arr_size = temp[-1]

    # If array is quarter size, expand to same size array as phase
    if float(arr_size) < 750:
        left *=2
        top *=2
        width *=2

    # Create circular mask
    r = (width / 2)
    a = top+r
    b = left+r
    xx,yy=np.ogrid[-a:X-a,-b:Y-b]
    mask = xx*xx + yy*yy < r*r
    '''
    # Set boundaries of mask
    tempx,tempy = np.where(mask)
    y_min = tempy.min()-border
    y_max = tempy.max()+border+1
    x_min = tempx.min()-border
    x_max = tempx.max()+border+1
    '''
    y_min = left+1-border
    y_max = left-1+width+border
    x_min = top+1-border
    x_max = top-1+width+border
    
    #print left, top, width
    #print y_min, y_max, x_min, x_max

    x1 = x_max - x_min
    y1 = y_max - y_min    
    size1 = np.array([x1,y1], dtype='int')
    m1 = mask[x_min:x_max,y_min:y_max]

    
    size_path = os.path.join(os.path.dirname(path), r'size.dat')
    size1.tofile(size_path)
    mask_path = os.path.join(os.path.dirname(path), r'mask.dat')
    m1.tofile(mask_path)


    if size:
        return mask, (x_min, x_max, y_min, y_max)
    else:
        return mask


if __name__ == '__main__':
    import sys
    
    file_ = r'test_data\test_h5.h5'
    border = 6
    size = False
    try:
        sys.stdout.write('Running get_mask(%s, border=%d, size=%s):'%(file_,border,size))
        for i in xrange(100):
            mask = get_mask(file_, border=border, size=size)
        print ' pass'
    except:
        print 'failed'
    '''
    size = True
    try:
        sys.stdout.write('Running get_mask(%s, border=%d, size=%s):'%(file_,border,size))
        mask, coord = get_mask(file_, border=border, size=size)
        print ' pass'
    except:
        print 'failed'
        y1, y2, x1, x2 = 50,100,50,100
        
    try:
        #mask = mask[x1:x2+1,y1:y2+1]
        mask = mask[coord[0]:coord[1],coord[2]:coord[3]]
        sys.stdout.write('mask.tofile save: ')
        mask.tofile(r'test_data\mask_binary.bin')
        print 'pass'
        sys.stdout.write('numpy.savetxt save: ')
        np.savetxt(r'test_data\mask_csv.csv', mask, delimiter=',', fmt='%d')
        print 'pass'
    except:
        print 'failed'
    '''
        
        
    
