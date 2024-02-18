"""
@author: Andrew Smith
Version 5 January 2024
"""

import math
import PySimpleGUI as sg
import sys
import json
import os
import traceback
from PIL import Image, ImageTk
import io
import datetime
from MEE2024util import resource_path, _version
import distortion_fitter


def check_files(files):
    try:
        for file in files:
            f=open(file, "rb")
            f.close()
    except:
        traceback.print_exc()
        raise Exception('ERROR opening file :'+file+'!')

def interpret_UI_values(options, ui_values, no_file = False):
    options['flag_display'] = ui_values['Show graphics']
    options['delete_saturated_blob'] = ui_values['delete_saturated_blob']
    options['centroid_gaussian_subtract'] = ui_values['centroid_gaussian_subtract']
    options['save_dark_flat'] = ui_values['save_dark_flat']
    options['float_fits'] = ui_values['float_fits']
    try : 
        options['m'] = int(ui_values['-m-']) if ui_values['-m-'] else 10
    except ValueError : 
        raise Exception('invalid m value')
    try : 
        options['n'] = int(ui_values['-n-']) if ui_values['-n-'] else 30
    except ValueError : 
        raise Exception('invalid n value!')
    try : 
        options['k'] = int(ui_values['-k-']) if ui_values['-k-'] else 10
    except ValueError : 
        raise Exception('invalid k value!')
    try : 
        options['pxl_tol'] = float(ui_values['-pxl_tol-']) if ui_values['-pxl_tol-'] else 5
    except ValueError : 
        raise Exception('invalid pxl_tol value!')
    try : 
        options['d'] = int(ui_values['-d-']) if ui_values['-d-'] else 10
    except ValueError : 
        raise Exception('invalid d value!')
    try : 
        options['centroid_gaussian_thresh'] = float(ui_values['-sigma_thresh-']) if ui_values['-sigma_thresh-'] else 7
    except ValueError : 
        raise Exception('invalid sigma_thresh value!')
    try : 
        options['min_area'] = int(ui_values['-min_area-']) if ui_values['-min_area-'] else 2
    except ValueError : 
        raise Exception('invalid min_area value!')
    try : 
        options['centroid_gap_blob'] = int(ui_values['-centroid_gap_blob-']) if ui_values['-centroid_gap_blob-'] else 20
    except ValueError : 
        raise Exception('invalid centroid_gap_blob value!')
    try : 
        options['blob_radius_extra'] = int(ui_values['-blob_radius_extra-']) if ui_values['-blob_radius_extra-'] else 100
    except ValueError : 
        raise Exception('invalid blob_radius_extra value!')
    try : 
        options['sigma_subtract'] = float(ui_values['sigma_subtract']) if ui_values['sigma_subtract'] else 2.5
    except ValueError : 
        raise Exception('invalid sigma_subtract value!')

    stack_files=ui_values['-FILE-'].split(';')
    dark_files=ui_values['-DARK-'].split(';') if ui_values['-DARK-'] else []
    flat_files=ui_values['-FLAT-'].split(';') if ui_values['-FLAT-'] else []
    options['database'] = ui_values['-DB-']
    options['output_dir'] = ui_values['output_dir']
    options['remove_edgy_centroids'] = ui_values['remove_edgy_centroids']
    if options['output_dir'] and not os.path.isdir(options['output_dir']):
        raise Exception('ERROR opening output folder :'+options['output_dir'])
    if not no_file:  
        check_files(stack_files)
        check_files(dark_files)
        check_files(flat_files)
        return [stack_files, dark_files, flat_files]


def interpret_UI_values2(options, ui_values):
    check_files([ui_values['-FILE2-']])
    options['output_dir'] = ui_values['output_dir2']
    options['flag_display'] = ui_values['Show graphics2']
    try : 
        options['max_star_mag_dist'] = float(ui_values['max_star_mag_dist']) if ui_values['max_star_mag_dist'] else 12
    except ValueError: 
        raise Exception('invalid max_star_mag_dist value!')
    try :
        _ = datetime.datetime.fromisoformat(ui_values['observation_date'])
        options['observation_date'] = ui_values['observation_date']
    except ValueError: 
        raise Exception('invalid obsveration date (use YYYY-MM-DD format)!')
    try : 
        options['distortion_fit_tol'] = float(ui_values['distortion_fit_tol']) if ui_values['max_star_mag_dist'] else 12
    except ValueError: 
        raise Exception('invalid distortion_fit_tol value!')
    
        
# ------------------------------------------------------------------------------
# use PIL to read data of one image
# ------------------------------------------------------------------------------


def get_img_data(f, maxsize=(30, 18), first=False):
    """Generate image data using PIL
    """
    try:
        img = Image.open(f)
        img.thumbnail(maxsize)
        if first:                     # tkinter is inactive the first time
            bio = io.BytesIO()
            img.save(bio, format="PNG")
            del img
            return bio.getvalue()
        return ImageTk.PhotoImage(img)
    except Exception:
        traceback.print_exc()
        print(f'note: error reading flag thumbnail file {f}')
        return None
    

def inputUI(options):
    popup_messages = {"no_file_error": "Error: file not entered! Please enter file(s)", "no_folder_error": "Error: Output folder not entered! Please enter folder"}
        
    sg.theme('Dark2')
    sg.theme_button_color(('white', '#500000'))

    layout_title = [
        [sg.Text('MEE 2024 Stacker UI', font='Any 14', key='MEE 2024 Stacker UI')],
    ]

    layout_file_input = [
        [sg.Text('File(s)', size=(7, 1), key = 'File(s)'), sg.InputText(default_text=options['workDir'],size=(75,1),key='-FILE-'),
         sg.FilesBrowse('Choose images to stack', key = 'Choose images to stack', file_types=(("Image Files (FIT, TIF, PNG)", "*.fit *.fts *.fits *.tif *tiff"),),initial_folder=options['workDir'])],
        [sg.Text('Dark(s)', size=(7, 1), key = 'Dark(s)'), sg.InputText(default_text='',size=(75,1),key='-DARK-'),
         sg.FilesBrowse('Choose Dark image(s)', key = 'Choose Dark image(s)', file_types=(("Image Files (FIT, TIF, PNG)", "*.fit *.fts *.fits *.tif *tiff"),),initial_folder=options['workDir'])],
        [sg.Text('Flat(s)', size=(7, 1), key = 'Flat(s)'), sg.InputText(default_text='',size=(75,1),key='-FLAT-'),
         sg.FilesBrowse('Choose Flat image(s)', key = 'Choose Flat image(s)', file_types=(("Image Files (FIT, TIF, PNG)", "*.fit *.fts *.fits *.tif *tiff"),),initial_folder=options['workDir'])],
        [sg.Text('Database', size=(7, 1), key = 'Database'), sg.InputText(default_text=options['database'],size=(75,1),key='-DB-'),
         sg.FilesBrowse('Choose Database', key = 'Choose Database', file_types=((".npz", "*.npz"),),initial_folder=options['workDir'])],
    ]

    layout_folder_output = [
        [sg.Text('Output folder (blank for same as input):', size=(50, 1), key = 'Output Folder (blank for same as input):')],
        [sg.InputText(default_text=options['output_dir'],size=(75,1),key='output_dir'),
            sg.FolderBrowse('Choose output folder', key = 'Choose output folder',initial_folder=options['output_dir'])],
    ]

    layout_base = [
    
    [sg.Checkbox('Show graphics', default=options['flag_display'], key='Show graphics'),
         sg.Checkbox('save_dark_flat', default=options['save_dark_flat'], key='save_dark_flat'),
         sg.Checkbox('float_32_fits', default=options['float_fits'], key='float_fits')],
    [sg.Text('Show the brightest stars in stack',size=(32,1), key='Show the brightest stars in stack'), sg.Input(default_text=str(options['d']),size=(8,1),key='-d-',enable_events=True)],
    [sg.Checkbox('Remove big bright object (blob)', default=options['delete_saturated_blob'], key='delete_saturated_blob')],
    [sg.Text('    blob_radius_extra',size=(32,1), key='blob_radius_extra'), sg.Input(default_text=str(options['blob_radius_extra']),size=(8,1),key='-blob_radius_extra-',enable_events=True)],
    [sg.Text('    centroid_gap_blob',size=(32,1), key='centroid_gap_blob'), sg.Input(default_text=str(options['centroid_gap_blob']),size=(8,1),key='-centroid_gap_blob-',enable_events=True)],
    [sg.Checkbox('Sensitive centroid finder mode (use if close to sun or moon; do not use for zenith or fields with >> 100 stars)', default=options['centroid_gaussian_subtract'], key='centroid_gaussian_subtract')],
    [sg.Text('    sigma_thresh [sensitive-mode]', key='sigma_thresh', size=(32,1)), sg.Input(default_text=str(options['centroid_gaussian_thresh']), key = '-sigma_thresh-', size=(8,1))],
    [sg.Text('    min_area (pixels) [sensitive-mode]', key='min_area (pixels)', size=(32,1)), sg.Input(default_text=str(options['min_area']), key = '-min_area-', size=(8,1))],
    [sg.Text('    sigma_subtract',size=(32,1)), sg.Input(default_text=str(options['sigma_subtract']),size=(8,1),key='sigma_subtract',enable_events=True)],
    [sg.Checkbox('Remove centroids near edges', default=options['remove_edgy_centroids'], key='remove_edgy_centroids')],
    [sg.Text('Advanced Parameters:', font=('Helvetica', 12))],
    [sg.Text('    m_stars_fit_stack', key='m_stars_fit_stack', size=(32,1)), sg.Input(default_text=str(options['m']), key = '-m-', size=(8,1))],
    [sg.Text('    n_stars_verify_stack',size=(32,1), key='n_stars_verify_stack'), sg.Input(default_text=str(options['n']),size=(8,1),key='-n-',enable_events=True)],
    [sg.Text('    pixel_tolerance',size=(32,1), key='pixel_tolerance'), sg.Input(default_text=str(options['pxl_tol']),size=(8,1),key='-pxl_tol-',enable_events=True)],
    [sg.Text('    k_stars_plate_solve',size=(32,1), key='k_stars_plate_solve'), sg.Input(default_text=str(options['k']),size=(8,1),key='-k-',enable_events=True)],
    [sg.Push(), sg.Button('OK'), sg.Cancel(), sg.Button("Open output folder", key='Open output folder', enable_events=True)]
    ]

    layout_distortion = [
        [sg.Text('File(s)', size=(7, 1), key = 'File2(s)'), sg.InputText(default_text=options['output_dir'],size=(75,1),key='-FILE2-'),
         sg.FilesBrowse('Choose data (FULL_DATA.xxx.npz)', key = 'Choose DATA_ALL file', file_types=(("npz files (.npz)", "*.npz"),),initial_folder=options['output_dir'])],
        
        [sg.Text('Output folder (blank for same as input):', size=(50, 1), key = 'Output Folder (blank for same as input):2')],
        [sg.InputText(default_text=options['output_dir'],size=(75,1),key='output_dir2'),
            sg.FolderBrowse('Choose output folder', key = 'Choose output folder',initial_folder=options['output_dir'])],
        [sg.Checkbox('Show graphics', default=options['flag_display'], key='Show graphics2')],
        [sg.Text('Maximum star magnitude',size=(32,1)), sg.Input(default_text=str(options['max_star_mag_dist']),size=(12,1),key='max_star_mag_dist',enable_events=True)],
        [sg.Text('Observation Date (YYYY-MM-DD)',size=(32,1)), sg.Input(default_text=str(options['observation_date']),size=(12,1),key='observation_date',enable_events=True)],
        [sg.Text('Distortion fit tolerance (as)',size=(32,1)), sg.Input(default_text=str(options['distortion_fit_tol']),size=(12,1),key='distortion_fit_tol',enable_events=True)],

        [sg.Push(), sg.Button('OK', key='OK2'), sg.Cancel(key='Cancel2'), sg.Button("Open output folder", key='Open output folder2', enable_events=True)]
    ]



    tab1_layout = layout_file_input + layout_folder_output + layout_base    
    tab2_layout = layout_distortion

    layout = [layout_title + [sg.TabGroup([[sg.Tab('Tab 1 - Find centroids', tab1_layout, key='-mykey-'),
                         sg.Tab('Tab 2 - Compute Distortion', tab2_layout),
                         ]],
                       key='-group2-', title_color='red',
                       selected_title_color='green', tab_location='top')
               ]]
    
    window = sg.Window('MEE2024 '+_version(), layout, finalize=True)
    window.BringToFront()

    def check_file(s):
        return s and not s == options['workDir']
    
    while True:
        event, values = window.read()
        if event==sg.WIN_CLOSED or event=='Cancel' or event=='Cancel2':
            window.close()
            return None

        if event=='Open output folder' or event=='Open output folder2':
            x = values['output_dir'].strip() if event=='Open output folder' else values['output_dir2'].strip()
            if not x:
                x = options['workDir']
            if x and os.path.isdir(x):
                path = os.startfile(os.path.realpath(x))
            else:
                sg.Popup(popup_messages['no_folder_error'], keep_on_top=True)
        if event=='OK2':
            if check_file(values['-FILE2-']):
                input_okay_flag = True
            else:
                # display pop-up file not entered
                input_okay_flag = False
                sg.Popup(popup_messages['no_file_error'], keep_on_top=True)
            if not values['output_dir2'].strip():
                input_okay_flag = False
                sg.Popup(popup_messages['no_folder_error'], keep_on_top=True)
            if input_okay_flag:
                try:
                    interpret_UI_values2(options, values)
                    distortion_fitter.match_and_fit_distortion(values['-FILE2-'], options, None)
                    print('Done!')
                    #sg.Popup('Done!', keep_on_top=True)
                except Exception as inst:
                    traceback.print_exc()
                    sg.Popup('Error: ' + str(inst.args[0]), keep_on_top=True)    
        if event=='OK':
            if check_file(values['-FILE-']):
                input_okay_flag = True
            else:
                # display pop-up file not entered
                input_okay_flag = False
                sg.Popup(popup_messages['no_file_error'], keep_on_top=True)
            if not values['output_dir'].strip():
                input_okay_flag = False
                sg.Popup(popup_messages['no_folder_error'], keep_on_top=True)
            
            if input_okay_flag:
                try:
                    files = interpret_UI_values(options, values)
                    window.close()
                    return files
                except Exception as inst:
                    traceback.print_exc()
                    sg.Popup('Error: ' + inst.args[0], keep_on_top=True)
                    
