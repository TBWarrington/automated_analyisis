import sys
import os
import glob
import csv
from io import StringIO
import re
from collections import OrderedDict
import time

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#import mpld3

def RunAnalysis(blank_file, input_file, layout):

	blank = ReformatData(blank_file)
	input = ReformatData(input_file)
	output = BarGraph(blank, input, layout)

	return output

def ReformatData(input_file):
	pattern = re.compile("Plate: Plate (\d+) - Wavelength: (\d+)")
	reading = re.compile("Reading: (\d+)")
	number = re.compile("\d+")
	df = pd.DataFrame(columns = ["plate", "A01", "A02", "A03", "A04", "A05", "A06", "A07","A08", "A09", "A10", "A11", "A12", "B01", "B02", "B03", "B04", "B05", "B06", "B07","B08", "B09", "B10", "B11", "B12", "C01", "C02", "C03", "C04", "C05", "C06", "C07","C08", "C09", "C10", "C11", "C12", "D01", "D02", "D03", "D04", "D05", "D06", "D07","D08", "D09", "D10", "D11", "D12", "E01", "E02", "E03", "E04", "E05", "E06", "E07","E08", "E09", "E10", "E11", "E12", "F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08", "F09", "F10", "F11", "F12", "G01", "G02", "G03", "G04", "G05", "G06", "G07", "G08", "G09", "G10", "G11", "G12", "H01", "H02", "H03", "H04", "H05", "H06", "H07", "H08", "H09", "H10", "H11", "H12", "wavelength", "timepoint"])

	dict = {}
	plate = 0
	wavelength = 0
	timepoint = 0
	row = []
	data = []
	with open(input_file, 'r' ) as theFile:
		reader = csv.reader(theFile, delimiter='\t')
		for line in reader:
			match = list(filter(pattern.match, line))
			if match:
				for element in match:
					thing = pattern.match(element)
					plate = int(thing.group(1))
					wavelength = int(thing.group(2))
					dict[wavelength] = {}
					data = [[plate]]
			reading_match = list(filter(reading.match, line))
			if reading_match:
				for element in reading_match:
					thing = reading.match(element)
					timepoint = int(thing.group(1))
					data = [[plate]]
			if list(filter(number.match, line)):
				row = list(filter(number.match, line))
				data.append(row)
				dict[wavelength][timepoint] = data
		for key, value in dict.items():
			for item, contents in value.items():
				flat_list = [val for sublist in dict[key][item] for val in sublist]
				flat_list.append(key)
				flat_list.append(item)
				df = df.append(pd.Series(flat_list, index=df.columns), ignore_index=True)
		df.sort_values(by=['plate', 'wavelength', 'timepoint'], inplace=True)
	df = df.astype(float)
	#df.to_csv("assay.csv", index=False)
	return df 

def BarGraph(blank, input, layout):

	samples, strains, conditions, zeroes, wavelengths = UnPack(layout)


#	wavelength = 525
	plate = 1
	timepoint = 0

	if timepoint == 0:
		T0 = blank
		T0.sort_index(axis=1, inplace=True)
#		T0 = T0.reset_index(drop=True)
		T1 = input
		T1.sort_index(axis=1, inplace=True)
#		T1 = T1.reset_index(drop=True)
	else:
		df = input
		T0 = df[(df.timepoint == 1)]
		T0 = T0.reset_index(drop=True)
		T1 = df[(df.timepoint == timepoint)]
		T1 = T1.reset_index(drop=True)
	blanked = pd.eval('T1 - T0')
	blanked.loc[blanked.index.isin(T0.index), ['plate', 'wavelength', 'timepoint']] = T1.loc[T0.index.isin(blanked.index), ['plate', 'wavelength', 'timepoint']].values

	blanked_prism = Prismize(blanked, samples, strains, conditions, wavelengths, plate, timepoint, "blanked")
	#print(blanked)

	average_blanked, sem_blanked = calc_avg(blanked, samples)
	normalized_blanked = normalize(blanked, samples, average_blanked, zeroes)
	normalized_prism = Prismize(normalized_blanked, samples, strains, conditions, wavelengths, plate, timepoint, "normalized")
	#print(normalized_blanked)

	average_normalized_blanked, sem_normalized_blanked = calc_avg(normalized_blanked, samples)
	output = GraphData(average_blanked, sem_blanked, average_normalized_blanked, sem_normalized_blanked, samples, strains, conditions, wavelengths, plate, timepoint)
	return output, blanked_prism, normalized_prism

def UnPack(file):
	samples = OrderedDict()
	zeroes = {}
	strains = []
	strain_list = []
	list = []
	wavelengths = {}
	df = pd.read_excel(file)
	#df = df.sort_values(["Strain", "Condition"])
	zero = ""
	for index, row in df.iterrows():
		sample_id = str(row["Strain"]) + "_" + str(row["Condition"]) + "_" + str(row["Unit"])
		samples[sample_id] = [x.strip() for x in row["Wells"].split(",")]
		wavelengths[sample_id] = row["Wavelength"]
		if str(row["Condition"]) == "0":
			zero = sample_id
		zeroes[sample_id] = zero
		condition = "Sample_" +str(row["Condition"]) + "_" + str(row["Unit"])
		list.append(condition)
		strain = str(row["Strain"])
		strains.append(strain)
	condition_list = set(list)
	condition_list = sorted(condition_list, key=lambda x: int(x.partition('Sample_')[2].partition('_')[0]))
	strain_list = set()
	strain_list = [x for x in strains if x not in strain_list and not strain_list.add(x)]
	return samples, strain_list, condition_list, zeroes, wavelengths

def calc_single_avg(df, sample_dict, sample_name):
	mean = df[sample_dict[sample_name]].mean(axis=1)
	sem = df[sample_dict[sample_name]].sem(axis=1)
	return mean, sem

def calc_avg(df, sample_dict):
	average_dict = pd.DataFrame()
	sem_dict = pd.DataFrame()
	for key in sample_dict:
		average_dict[key], sem_dict[key] = calc_single_avg(df, sample_dict, key)
	average_dict.sort_index(axis=1, inplace=True)
	average_dict = average_dict.reset_index(drop=True)
	average_dict[['plate', 'wavelength', 'timepoint']] = df[['plate', 'wavelength', 'timepoint']]
	sem_dict.sort_index(axis=1, inplace=True)
	sem_dict = sem_dict.reset_index(drop=True)
	sem_dict[['plate', 'wavelength', 'timepoint']] = df[['plate', 'wavelength', 'timepoint']]
	return average_dict, sem_dict

def normalize(df, sample_dict, average_dict, zeroes):
	normalized_dict = pd.DataFrame()
	for key in sample_dict:
		for i in range(len(sample_dict[key])):
			normalized_dict[sample_dict[key][i]] = df[sample_dict[key][i]].div(average_dict[zeroes[key]].values,axis=0)
	normalized_dict.sort_index(axis=1, inplace=True)
	normalized_dict = normalized_dict.reset_index(drop=True)
	normalized_dict[['plate', 'wavelength', 'timepoint']] = df[['plate', 'wavelength', 'timepoint']]
	return normalized_dict

def Prismize(data, samples, strains, conditions, wavelengths, plate, timepoint, name):
	concentrations = []
	for condition in conditions:
		concentrations.append(condition.partition('Sample_')[2])
	output_data = pd.DataFrame(index=concentrations)
	output_data = output_data.fillna('')
	for condition in concentrations:
		for sample in samples:
			for well in range(len(samples[sample])):
				column = sample.partition('_')[0] + "-" + str(well+1)
				if int(condition.partition('_')[0]) == int(sample.partition('_')[2].partition('_')[0]):
					wavelength = wavelengths[sample]
					query = data.query('wavelength == @wavelength and timepoint == @timepoint and plate == @plate')[samples[sample][well]].iloc[0]
					output_data.loc[condition, column] = query
	output = name + time.strftime("%Y%m%d-%H%M%S") + '.csv'
	output_data.to_csv(os.path.join('./uploads', output)) #local version
	#output_data.to_csv(os.path.join('/home/FREDsense/automated_analysis/uploads', output)) #online version
	return output

def GraphData(average_blanked, sem_blanked, average_normalized_blanked, sem_normalized_blanked, samples, strains, conditions, wavelengths, plate, timepoint):

	average_normalized_blanked_dict = OrderedDict()
	sem_normalized_blanked_dict = OrderedDict()
	average_blanked_dict = OrderedDict()
	sem_blanked_dict = OrderedDict()

	for condition in conditions:
		for sample in samples:
			if int(condition.partition('Sample_')[2].partition('_')[0]) == int(sample.partition('_')[2].partition('_')[0]):
				wavelength = wavelengths[sample]
#				print(sample)
				average_normalized_blanked_query = average_normalized_blanked.query('wavelength == @wavelength and timepoint == @timepoint and plate == @plate')[sample].iloc[0]
				sem_normalized_blanked_query = sem_normalized_blanked.query('wavelength == @wavelength and timepoint == @timepoint and plate == @plate')[sample].iloc[0]
				average_blanked_query = average_blanked.query('wavelength == @wavelength and timepoint == @timepoint and plate == @plate')[sample].iloc[0]
				sem_blanked_query = sem_blanked.query('wavelength == @wavelength and timepoint == @timepoint and plate == @plate')[sample].iloc[0]
#				if average_normalized_blanked_query > y_max:
#					y_max = average_normalized_blanked_query
#				if average_blanked_query > y_max:
#					y_max = average_normalized_blanked_query
				if condition in average_blanked_dict:
					average_normalized_blanked_dict[condition].append(average_normalized_blanked_query)
					sem_normalized_blanked_dict[condition].append(sem_normalized_blanked_query)
					average_blanked_dict[condition].append(average_blanked_query)
					sem_blanked_dict[condition].append(sem_blanked_query)
				else:
					average_normalized_blanked_dict[condition] = [average_normalized_blanked_query]
					sem_normalized_blanked_dict[condition] = [sem_normalized_blanked_query]
					average_blanked_dict[condition] = [average_blanked_query]
					sem_blanked_dict[condition] = [sem_blanked_query]


	# set width of bar
	barWidth = 0.2
 
	# Set position of bar on X axis
	r1 = np.arange(len(average_blanked_dict[conditions[0]]))
	r2 = [x + barWidth for x in r1]
	r3 = [x + barWidth for x in r2]
	r4 = [x + barWidth for x in r3]
	r5 = [x + barWidth for x in r4]
	r6 = [x + barWidth for x in r5]

	positions = [r1, r2, r3, r4, r5, r6]
	#colours = ['#7f6d5f','#557f2d','#2d7f5e','#2d7f5e']
	colours = ['C0','C1','C3','C4', 'C5', 'C6']

	figure = plt.figure(1)
	#plt.subplots(2,1)
	plt.subplot(2, 1, 1)
	for number, condition in enumerate(conditions):
		plt.bar(positions[number], average_normalized_blanked_dict[condition], yerr=sem_normalized_blanked_dict[condition], capsize=barWidth*20, color=colours[number], width=barWidth, edgecolor='white', label=str(condition.partition('_')[2]))
	plt.title('Normalized Signal')
	plt.ylabel('Normalized Signal')
	plt.xticks([r + barWidth for r in range(len(average_blanked_dict[conditions[0]]))], strains)
	plt.legend(bbox_to_anchor=(0.95, 1)) #Originally 1,1 colour bars didn't show correctly



#	# Set position of bar on X axis
#	r1 = np.arange(len(Sample_0_ppb_raw))
#	r2 = [x + barWidth for x in r1]
#	r3 = [x + barWidth for x in r2]
#	r4 = [x + barWidth for x in r3]


	#plt.figure(2)
	plt.subplot(2, 1, 2)
	# Make the plot
	for number, condition in enumerate(conditions):
		plt.bar(positions[number], average_blanked_dict[condition], yerr=sem_blanked_dict[condition], capsize=barWidth*20, color=colours[number], width=barWidth, edgecolor='white', label=str(condition.partition('_')[2]))

	plt.title('Raw Signal')
	plt.ylabel('Signal')
	plt.xticks([r + barWidth for r in range(len(average_blanked_dict[conditions[0]]))], strains)
	plt.legend(bbox_to_anchor=(0.95, 1)) #Originally 1,1 colour bars didn't show

	new_rc_params = {'text.usetex': False, "svg.fonttype": 'none'}
	plt.rcParams.update(new_rc_params)

	output = time.strftime("%Y%m%d-%H%M%S") + '.svg'
	#plt.savefig(os.path.join('/home/FREDsense/automated_analysis/uploads', output)) #online version
	plt.savefig(os.path.join('./uploads', output)) #local version
	#plt.figure(figsize=(8.5,11))
	#return mpld3.fig_to_html(figure)
	#plt.show()
	plt.gcf().clear()
	return output
#mpld3.show()


