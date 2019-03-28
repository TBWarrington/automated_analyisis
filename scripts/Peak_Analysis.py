import os
import ntpath

import numpy as np
import pandas as pd
from scipy import signal
from matplotlib import pyplot as plt
from galvani.BioLogic import MPRfile

#path = sys.argv[1]
path = '/mnt/c/Users/Tim/Google Drive/Work/Python/BioLogic'
#path = '/storage/emulated/0/Download/Sync/Work/Python/BioLogic'
output_file = 'test.txt' #sys.argv[2]
output_file_path = os.path.join(path, output_file)


def find_nearest(array,value):
	idx = (np.abs(array-value)).argmin()
	return array[idx]

def PeakHeight(ewe_v, current, filename):
#smooth curve
	yhat = signal.savgol_filter(current, 99, 3) # window size 51, polynomial order 3, window 99 seems to give better peak detection on noisy data

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
	maxima_x = ewe_v.iloc[maxima_index]
	#maxima_x = ewe_v[maxima_index]
	
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

	plot_graph(ewe_v, current, yhat, maxima_x, maxima_y, fit_fn, filename)
	return peak_height

#skips lines in header until it reaches line starting with "line", corresponds to first column name
def skip_to(fle, line,**kwargs):
	if os.stat(fle).st_size == 0:
		raise ValueError("File is empty")
	with open(fle, encoding="latin-1") as f:
		pos = 0
		cur_line = f.readline()
		while not cur_line.startswith(line):
			pos = f.tell()
			cur_line = f.readline()
		f.seek(pos)
		return pd.read_csv(f, **kwargs)

def runAnalysis(path, output_file):
	output = []
	output_df = pd.DataFrame(columns = ["Sample Name", "Peak Height"])
	for filename in path:
		if filename != output_file[0]:
			#df = skip_to(filename, "mode", sep="\t")
			#ewe_v = df['Ewe/V'].loc[df['cycle number'] == 3.000000000000000E+000]
			#current = df['<I>/mA'].loc[df['cycle number'] == 3.000000000000000E+000]
			mpr = MPRfile(filename)
			df = pd.DataFrame.from_records(mpr.data)
			ewe_v = df['Ewe/V'].loc[df['cycle number'] == 3.0]
			current = df['I/mA'].loc[df['cycle number'] == 3.0]
			peak_height = PeakHeight(ewe_v, current, filename)
			string = ntpath.basename(filename) + ',' + str(peak_height) + ',\n'
			output.append(string)
			print("Peak height for " + ntpath.basename(filename) + " is " + str(peak_height))
			output_df.loc[len(output_df)] = [ntpath.basename(filename), peak_height]
	output_df.to_csv(output_file, index=False, float_format='%.5e')
#	output_df = output_df.set_index("Sample Name").T
#	output_df.to_csv(output_file + "_transposed.csv", index=False)
	return path

def plot_graph(x, y, yhat, maxima_x, maxima_y, fit_fn, filename):
	#raw data
	plt.plot(x, y)
	#smoothed data
	plt.plot(x,yhat)#, color='red')
	#baseline
	plt.plot(x, fit_fn(x))
	#peak
	plt.scatter(maxima_x, maxima_y, color='red')
	plt.xlabel('Ewe/V')
	plt.ylabel('<I>/mA')
	output = ntpath.basename(filename) + ".png"
	#plt.savefig(os.path.join('/home/FREDsense/automated_analysis/uploads', output)) #online version
	plt.savefig(os.path.join('./uploads', output)) #local version
	plt.gcf().clear()
	#plt.show()


