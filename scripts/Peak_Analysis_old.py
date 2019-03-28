import sys
import csv
import re
import ntpath

import numpy as np
import pandas as pd
from scipy import signal, interpolate

import pandas as pd

#from PyQt5 import QtWidgets, QtCore

path = []
output_file = []
output = []


#ewe_v is x axis
#current is y axis

def find_nearest(array,value):
	idx = (np.abs(array-value)).argmin()
	return array[idx]

def PeakHeight(ewe_v, current):
#smooth curve
	yhat = signal.savgol_filter(current, 51, 3) # window size 51, polynomial order 3

#convert to numpy array
	ewe_v_array = np.array(ewe_v)
	current_array = np.array(yhat)

#calculate first derivative
	ewe_v_diff = np.diff(ewe_v_array)
	current_diff = np.diff(current_array)
	np.seterr(divide='ignore', invalid='ignore') #ignore divide by zero error: doesn't seem to be a problem as long as it is not a critical value
	diff = current_diff/ewe_v_diff
	diff_smoothed = signal.savgol_filter(diff, 51, 3) # window size 51, polynomial order 3

#calculate second derivative
#	second_diff = np.diff(diff_smoothed)/ewe_v_diff[0:len(diff)-1]
#	sec_diff_smoothed = signal.savgol_filter(second_diff, 51, 3) # window size 51, polynomial order 3


#find peak maxima
	#use data points 50-500: eliminates noise at edges
	maxima = find_nearest(diff_smoothed[50:500], 0) 
	maxima_index = diff_smoothed.tolist().index(maxima)
	maxima_y = yhat[maxima_index]
	maxima_x = ewe_v[maxima_index]
	
#find peak maxima using interpolation to get exact y intercept of derivative - Missed peak on at least one occation. Seems to make little difference otherwise.
	#	yToFind = 0
#	yreduced = diff_smoothed[50:500]# - yToFind
#	freduced = interpolate.UnivariateSpline(ewe_v_array[50:500], yreduced, s=0)
#	maxima_x = freduced.roots()[0]

#	y_interp = interpolate.UnivariateSpline(ewe_v_array[50:500], current_array[50:500], s=0)
#	maxima_y = y_interp(maxima_x)

#calculate baseline
	#uses points 50-150: captures linear part of graph
	x_linear = ewe_v[50:150]
	y_linear = current[50:150]
	fit = np.polyfit(x_linear, y_linear, 1)
	fit_fn = np.poly1d(fit)

#calculate peak height (peak maxima minus baseline)
	base_y = (fit[0] * maxima_x) + fit[1]
	peak_height = maxima_y - base_y

	return peak_height

def runAnalysis(path, output_file):
	output = []
	df = pd.DataFrame(columns = ["Sample Name", "Peak Height"])
	for filename in path:
		if filename != output_file[0]:
			with open(filename, 'rU',  encoding="latin-1") as o_file: #python3
				ewe_v = []
				current = []
				for _ in range(62): #.mpt header is 57 lines long (includes legend) Some files have header 58 lines long. Will lose unused data point on some files but prevents error, V11.21 has 59 line header, Ugh! 60 now...
					next(o_file) # skip headings
				reader=csv.reader(o_file,delimiter='\t')
				try:
					for m, o, e, cc, c, t, cv, v, i, cn, q, p in reader:
						if float(cn) == 3: #and float(o) == 1:
							ewe_v.append(float(v))
							current.append(float(i))
				except:
					for m, o, e, cc, c, t, cv, v, i, cn, q, irange, p in reader: #new version has more values for some reason...
						if float(cn) == 3: #and float(o) == 1:
							ewe_v.append(float(v))
							current.append(float(i))
				peak_height = PeakHeight(ewe_v, current)
#				string = filename + '\t' + str(peak_height) + '\n'
				string = ntpath.basename(filename) + ',' + str(peak_height) + ',\n'
				output.append(string)
				print("Peak height for " + ntpath.basename(filename) + " is " + str(peak_height))
				df.loc[len(df)] = [ntpath.basename(filename), str(peak_height)]
	#df = pd.DataFrame(output)
	#print(df)
	df.to_csv(output_file, index=False)
	df_transposed = df.transpose()
	df_transposed.to_csv(output_file + "_transposed", index=False)
#	with open(output_file, 'w', newline='\n') as w_file:
#		for string in output:
#			w_file.write(string)
#		output = []
#	print("Done!")
#	del path[:len(path)]
	return path

#	sys.exit()

