from __future__ import print_function
from tkinter import *
from win32.win32api import GetShortPathName
from PIL import Image
from scipy.misc import toimage
from multiprocessing.pool import Pool
from tkinter.filedialog import askdirectory
import re
import os
import time
import numpy as np

from wrapped_phase import get_phase, get_path
from unwrap_phase import unwrap_setup, unwrap
from zernike_js import get_zernike
from mask import get_mask

#Libraries required:
# Tk, easygui, win32api, time, ImageTk, Image, scipy, numpy, pyplot, Tm
#Files required in same directory:
# wrapped_phase.py, unwrap_phase.py, zernike_js.py, calc_phase.py, mask.py


#Extract phase using 9-bin algorithm
def phase():

    #Create window
    win = Toplevel()
    win.wm_title('Extracting phase')

    #Current file number label
    t = StringVar()
    t.set('0')
    info = Label(win, textvariable=t)
    info.grid(row=0)

    #Close button display 'working'
    t1 = StringVar()
    t1.set('working')
    b1 = Button(win, textvariable=t1, command=win.destroy)
    b1.grid(row=1)

    #Get path, filenames, and mask setup
    path = path_entry.get()
    path_raw, path_images, filenames = get_path(path, filetype='h5')
    first_file = os.path.join(path, filenames[0])
    mask, coord = get_mask(first_file, border=0)
    mask = mask[coord[0]:coord[1], coord[2]:coord[3]]

    #Draw window widgets
    maxf = str(len(filenames))
    t.set('0/' + maxf)
    win.update()

    #Setup summary string
    summary = 'x size,' + str(coord[1]-coord[0]) + '\n'
    summary += 'y size,' + str(coord[3]-coord[2]) + '\n'
    summary += 'number of files,' + str(len(filenames)) + '\n'
    summary += 'file, instensity, modulation\n'

    #Run 9-bin phase wrap
    i = 0
    A = []
    zz = time.clock()
    pool = Pool(processes=8)

    for filename in filenames:
        A.append((filename, path, path_raw, path_images, mask, coord))

    for x in pool.map(get_phase, A):
        t.set(str(i) + '/' + maxf)
        win.update()
        i += 1
        summary += x

    zz = time.clock() - zz
    pool.close()

    #Print summary and save to ./debug.csv
    print(summary)
    f_debug = os.path.join(path, 'debug.csv')
    f_debug = open(f_debug, 'w')
    f_debug.write(summary)
    f_debug.close()

    #Display runtime and change close button text to 'close'
    t1.set('Close')
    t.set('Finished in %f seconds' % zz)
#End phase()


#Unwrap phase with selected algorithm
#   parent = algorithm choice window
#   listb = list button with choosen unwrap algorithm
#   win_show = boolean to show process window
def start_unwrap(parent, listb, win_show):

    #Get algorthim .exe file then destroy parent window
    exe_name = listb.get(listb.curselection())
    exe = r'C:\phase\\' + listb.get(listb.curselection()) + '_o2.exe'
    parent.destroy()

    #Create window
    win = Toplevel()
    win.wm_title('Unwrapping phase')

    #Label showing .exe file being run
    exe_label = Label(win, text=exe)
    exe_label.grid(row=0)

    #Current file number label
    t = StringVar()
    t.set('Starting')
    num_label = Label(win, textvariable=t)
    num_label.grid(row=1)

    #Close button display 'working'
    t1 = StringVar()
    t1.set('working')
    b1 = Button(win, textvariable=t1, command=win.destroy)
    b1.grid(row=2)

    #Draw window widgets
    win.update()

    #Get path and filenames
    path = path_entry.get()
    path_raw, path_images, filenames = get_path(path, filetype='wrapped')

    #Get array size and summary string from file
    row_size, col_size, data = unwrap_setup(path)
    data[3] += ','+exe_name + ' rms'

    #Run unwrap
    i = 0
    maxf = str(len(filenames))
    t.set(str(i) + '/' + maxf)
    win.update()
    zz = time.clock()

    pool = Pool(processes=10)

    A = []
    for filename in filenames:
        A.append((filename, path, path_raw, path_images, exe, row_size, col_size, bool(win_show)))
    imap1 = pool.imap(unwrap, A)
    pool.close()
    for x in imap1:
        i += 1
        t.set(str(i) + '/' + maxf)
        win.update()
        data[i+3] += x
    zz = time.clock() - zz

    #Print summary and update ./debug.csv
    f1 = os.path.join(path, r'debug.csv')
    f1 = open(f1, 'w')
    for a in data:
        f1.write(a + '\n')
        print(a)
    f1.close()

    #Display runtime and change close button text to 'close'
    t1.set('Close')
    t.set('Finished in %f seconds' % zz)
#End start_unwrap(parent,listb,win_show)


#Runs a zernike fit from j = (1 to mode) using Noll indexing
#   mode = int Noll index
def zernike(mode):

    #Setup window
    win = Toplevel()
    win.wm_title('Zernike')

    #Current file number label
    t = StringVar()
    t.set('Starting')
    num_label = Label(win, textvariable=t)
    num_label.grid(row=1)

    #Close button display 'working'
    t1 = StringVar()
    t1.set('working')
    b1 = Button(win, textvariable=t1, command=win.destroy)
    b1.grid(row=2)

    #Draw window widgets
    win.update()

    #Get path, filenames,  and setup mask
    path = path_entry.get()
    path_raw, path_images, filenames = get_path(path, filetype='unwrapped')
    path_size = os.path.join(path, r'size.dat')
    [xsize, ysize] = np.fromfile(path_size, dtype='int')
    size = xsize, ysize
    mask_file = os.path.join(path, 'mask.dat')
    fm = open(mask_file, 'rb')
    mask = np.fromfile(fm, dtype='bool')
    fm.close()
    mask.resize(size)

    #Setup summary string
    temp = 'piston, tilt, astig, power, sphere, err[0], err[1], err[2]\n'

    #Run zernike fit
    i = 0
    maxf = str(len(filenames))
    t.set(str(i) + '/' + maxf)
    win.update()
    zz = time.clock()

    A = []
    summary = '{}\nModes,{}\nfile, piston, tilt, astig, power, sphere, err[0], err[1], err[2], rms, coma\n'.format(path, mode)

    for filename in filenames:
        A.append((filename, path, path_raw, path_images, mask, size, mode))
    map_result = map(get_zernike, A)

    for x in map_result:
        i += 1
        t.set(str(i) + '/' + maxf)
        win.update()
        summary += x
    zz = time.clock() - zz

    #Print summary
    f1 = os.path.join(path, r'zernike.csv')
    f1 = open(f1, 'w')
    f1.write(summary)
    print(summary)
    f1.close()

    #Display runtime and change close button text to 'close'
    t1.set('Close')
    t.set('Finished in %f seconds' % zz)
#End zernike(mode)


# Gets what unwrap algorithm to use and whether to show the subprocess window
def unwrap_options():

    # Get the path then check if empty
    path = path_entry.get()
    if not path:
        return

    #Setup window
    win = Toplevel()
    win.wm_title('Unwrap algorithms')

    # Create listbox and populate with options for unwrapping
    listb = Listbox(win)
    listb.grid(row=0)
    for item in ['flynn', 'fmg', 'gold', 'lpno', 'mcut', 'pcg', 'qual', 'unmg', 'unwt']:
        listb.insert(END, item)

    # Create a check box for whether to show the subprocess window for each unwrap call
    win_show = BooleanVar()
    win_show_box = Checkbutton(win, text="Show process window", variable=win_show)
    win_show_box.grid(row=1)

    # Create a button to call start_unwrap with the choosen algorithm
    b4 = Button(win, text='list', command=lambda: start_unwrap(win, listb, win_show.get()))
    b4.grid(row=2)
# End unwrap_options()
    

# Gets the number of indices to build the zernike to
def zernike_options():

    # Get the path then check if empty
    path = path_entry.get()
    if not path:
        return

    #Setup window
    win = Toplevel()

    z_label = Label(win, text='nmode = ')
    z_label.grid(row=0, column=0)

    # Create text entry for zernike mode
    entry_z = Entry(win, textvariable=zernike_mode)
    entry_z.grid(row=0, column=1)

    # Create button to call test_zmode
    runZernike = Button(win, text='Ok', command=lambda: test_zmode(win))
    runZernike.grid(row=1, columnspan=2)
# End zernike_options()


def test_zmode(self):
    tmp = zernike_mode.get()

    try:
        if int(tmp) < 1 or int(tmp) > 9999:
            tmp = 'a'
        mode = int(tmp)
    except:
        tkMessageBox.showerror('Error', 'Invalid input, integer between 1 and 100')
        self.focus_set()
        return

    # Destroy window and run zernike after checking input, otherwise errors in zernike are masked
    self.destroy()
    zernike(mode)


def phase_options():
    #Only run when there is a path chosen
    path = path_entry.get()

    if not path:
        return

    phase()


#Get directory to process, saves to path_entry
def get_directory():
    #path = diropenbox('Pick directory to process',default=r'c:\phase')
    path = askdirectory()
    #Avoids a crash if the directory window is closed without choosing a directory
    try:
        #Unwrap call is a CMD.exe call so spaces in path name will crash the call
        #GetShortPathName returns 8.3 compatable file name
        path = GetShortPathName(path)
        path_entry.set(path)
    except:
        pass


# Make a window with unwrapped surface and zernike fit removed of the first image of the dataset
def check_zernike_surface():

    #f_surface = r'C:\Documents and Settings\jsaredy\Desktop\thresh\images\surface\surface_00001.bmp'
    #f_zernike = r'C:\Documents and Settings\jsaredy\Desktop\thresh\images\zernike\zernike_diff_00001.bmp'
    # Get path from root window
    #Only run when there is a path chosen
    path = path_entry.get()

    if not path:
        return
    f_surface = os.path.join(path, r'images\surface\surface_00001.bmp')
    f_zernike = os.path.join(path, r'images\zernike\zernike_diff_00001.bmp')

    draw_2images(f_surface, f_zernike)
#End check_zernike_surface()


# Make a window with unwrapped surface and zernike fit removed of the first image of the dataset
def draw_2images(surface_file1, surface_file2):

    win = Toplevel()

    # Create PhotoImage of surfaces
    image_surface1 = Image.open(surface_file1)
    tkpi_surface1 = ImageTk.PhotoImage(image_surface1)
    del image_surface1

    image_surface2 = Image.open(surface_file2)
    tkpi_surface2 = ImageTk.PhotoImage(image_surface2)
    del image_surface2

    # Draw images
    label_1 = Label(win, text=surface_file1)
    label_1.grid(row=1, column=0)
    label_image_surface1 = Label(win, image=tkpi_surface1)
    label_image_surface1.image = tkpi_surface1  # required for Tk to maintain reference
    label_image_surface1.grid(row=0, column=0)

    label_2 = Label(win, text=surface_file2)
    label_2.grid(row=1, column=1)
    label_image_surface2 = Label(win, image=tkpi_surface2)
    label_image_surface2.image = tkpi_surface2  # required for Tk to maintain reference
    label_image_surface2.grid(row=0, column=1)

    # Close
    test_destroy = Button(win, text='Close', command=win.destroy)
    test_destroy.grid(row=2)
#End check_zernike_surface()


if __name__ == '__main__':
    root = Tk()
    root.wm_title('TFI phase unwrapping')

    zernike_mode = StringVar()
    zernike_mode.set('15')

    exe_name = StringVar()
    f1 = Frame(root)
    f1.grid(row=0, columnspan=4)

    path_entry = StringVar()
    entry1 = Entry(f1, textvariable=path_entry, width=70)
    entry1.grid(row=0)

    directory_button = Button(f1, text="get dir", command=get_directory)
    directory_button.grid(row=0, column=1, padx=5)

    b2 = Button(root, text="Calc phases", command=phase_options)
    b2.grid(row=1)

    quitButton = Button(root, text='Close', command=root.destroy)
    quitButton.grid(row=2)

    b3 = Button(root, text='Unwrap', command=unwrap_options)
    b3.grid(row=1, column=1)

    b_zern = Button(root, text='Zernike', command=zernike_options)
    b_zern.grid(row=1, column=2)

    #b4 = Button(root, text='test', command=check_zernike_surface)
    #b4.grid(row=3, column=1)

    root.mainloop()
