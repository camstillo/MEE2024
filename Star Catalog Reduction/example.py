import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns
 
def parse_input_file(filename):
    data = pd.read_csv(filename, delimiter='|', engine='python', compression='gzip',
                   skiprows=11, 
                   skipfooter=1,
                   index_col=0,
                   header=0,
                   usecols=[1, 4, 7, 9, 10, 11, 12, 13, 14, 15, 16],
                   names=['index', 'magnitude', 'raw position', 'parallax', 
                          'proper motion alpha', 'proper motion delta',
                          'error alpha', 'error delta', 'error parallax',
                          'error motion alpha', 'error motion delta'])
     
    # convert position string into two floats for the two position coordinates
    data = parse_raw_position(data)
     
    # remove rows with NaN values (data missing)
    data.dropna(inplace=True)
   
    # convert all miliarcsecond values to degrees
    data = convert_to_degrees(data)
     
    # reinterpret magnitude values as floats
    data['magnitude'] = data['magnitude'].astype(float)
     
    return data

def parse_raw_position(data):
    data[['alpha', 'delta']] = (
        data['raw position']
        .str.split(expand=True)
        .astype(float)
    )
     
    # drop original column
    data.drop('raw position', axis=1, inplace=True)
    return data

def convert_to_degrees(data):
    columns = ['parallax', 'proper motion alpha', 'proper motion delta',
               'error alpha', 'error delta', 'error parallax',
               'error motion alpha', 'error motion delta']
     
    # divide all miliarcsecond values by 3600 and 1000 to converto to degrees
    for column in columns:
        data[column] = data[column].astype(float) / 3600000.0
     
    return data




# runtime code
data = parse_input_file('http://cdsarc.u-strasbg.fr/viz-bin/nph-Cat/txt.gz?I/239/hip_main.dat')
 
plt.hist2d(data['alpha'], data['delta'], bins=125, cmap='Blues')
plt.xlabel('ascension (°)')
plt.ylabel('declination (°)')
plt.xticks([0, 60, 120, 180, 240, 300, 360])
plt.yticks([-90, -60, -30, 0, 30, 60, 90])
plt.show()

