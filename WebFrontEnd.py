import os, shutil
from flask import Flask, flash, request, redirect, url_for, send_from_directory, render_template, make_response, jsonify
from werkzeug import SharedDataMiddleware
from werkzeug.utils import secure_filename
from werkzeug.datastructures import CombinedMultiDict

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired

import tablib as tb

from scripts.BarGraph import RunAnalysis
from scripts.input_form import Index, InputForm, EC, Form, RodeoStat
from scripts.Peak_Analysis import runAnalysis
from scripts.RodeoStat_Peak_Analysis import runRodeoStatAnalysis
import time

from flask_httpauth import HTTPBasicAuth

IMAGE_FOLDER = './uploads' #local version
#IMAGE_FOLDER = '/uploads/' #online version
UPLOAD_FOLDER = './uploads' #local version
#UPLOAD_FOLDER = '/home/FREDsense/automated_analysis/uploads' #online version
#ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'fa'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['IMAGE_FOLDER'] = IMAGE_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'

auth = HTTPBasicAuth()
 
@auth.get_password
def get_password(username):
	if username == 'fredsense':
		return 'data'
	return None
 
@auth.error_handler
def unauthorized():
	return make_response(jsonify( { 'error': 'Unauthorized access' } ), 403)
	# return 403 instead of 401 to prevent browsers from displaying the default auth dialog


def allowed_file(filename):
	return '.' in filename and \
			filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
#@auth.login_required
def index():
	form = Index()

	if form.validate_on_submit():
		if form.ec_button.data:
			return redirect('/ec')
		elif form.rodeostat_button.data:
			return redirect('/rodeostat')
		elif form.microplate_button.data:
			return redirect('/microplate')
		elif form.instructions_button.data:
			return redirect('/instructions')
		else:
			return render_template('index.html', form=form)

	return render_template('index.html', form=form)

@app.route('/ec', methods=['GET', 'POST'])
#@auth.login_required
def ec_assay():
	form = EC(CombinedMultiDict((request.files, request.form)))
	file_filenames = []
	image_filenames = []
	form2 = Form(image_filenames)
	delete_files()
	if form.validate_on_submit():
		if form.data_file.data != ['']:
			for file in form.data_file.data:
				file_filename = secure_filename(file.filename)
				#data.save(os.path.join(app.config['UPLOAD_FOLDER'], data_filename))
				file_filenames.append(os.path.join(app.config['UPLOAD_FOLDER'], file_filename))
				image_filenames.append(os.path.join(app.config['IMAGE_FOLDER'], file_filename))
				file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_filename))
			form2 = Form(image_filenames)
			timestamp = os.path.join(app.config['UPLOAD_FOLDER'], time.strftime("%Y%m%d-%H%M%S") + '.csv')
			output = runAnalysis(file_filenames, timestamp)
			raw = tb.Dataset().load(open(timestamp).read())
			raw_data = raw.html
			transposed = raw.transpose()
			try:
				transposed_data = transposed.html
			except AttributeError:
				transposed_data = None
			return render_template('input_form.html', form=form, form2=form2, result=None, normal_prism=None, raw_prism=transposed_data, raw_data=raw_data)

	return render_template('input_form.html', form=form, form2=form2, result=None, normal_prism=None, raw_prism=None, raw_data=None)

@app.route('/rodeostat', methods=['GET', 'POST'])
#@auth.login_required
def rodeostat_assay():
	form = RodeoStat(CombinedMultiDict((request.files, request.form)))
	file_filenames = []
	image_filenames = []
	form2 = Form(image_filenames)
	delete_files()
	if form.validate_on_submit():
		if form.data_file.data != ['']:
			for file in form.data_file.data:
				file_filename = secure_filename(file.filename)
				#data.save(os.path.join(app.config['UPLOAD_FOLDER'], data_filename))
				file_filenames.append(os.path.join(app.config['UPLOAD_FOLDER'], file_filename))
				image_filenames.append(os.path.join(app.config['IMAGE_FOLDER'], file_filename))
				file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_filename))
			form2 = Form(image_filenames)
			timestamp = os.path.join(app.config['UPLOAD_FOLDER'], time.strftime("%Y%m%d-%H%M%S") + '.csv')
			output = runRodeoStatAnalysis(file_filenames, timestamp)
			raw = tb.Dataset().load(open(timestamp).read())
			raw_data = raw.html
			transposed = raw.transpose()
			try:
				transposed_data = transposed.html
			except AttributeError:
				transposed_data = None
			return render_template('input_form.html', form=form, form2=form2, result=None, normal_prism=None, raw_prism=transposed_data, raw_data=raw_data)

	return render_template('input_form.html', form=form, form2=form2, result=None, normal_prism=None, raw_prism=None, raw_data=None)

@app.route('/microplate', methods=['GET', 'POST'])
#@auth.login_required
def microplate_assay():
	form = InputForm(CombinedMultiDict((request.files, request.form)))
	form2 = Form([])
	delete_files()
	if form.validate_on_submit():
#		os.remove(os.path.join(app.config['UPLOAD_FOLDER'], "figure.png"))
		blank = form.blank_file.data
		data = form.data_file.data
		layout = form.layout_file.data
		blank_filename = secure_filename(blank.filename)
		data_filename = secure_filename(data.filename)
		layout_filename = secure_filename(layout.filename)
		print(blank_filename)
		print(data_filename)
		print(layout_filename)
		#print(form.name.data)
		#print(form.cond.data)
		#print(form.unit.data)
		#print(form.wells.data)
		blank.save(os.path.join(app.config['UPLOAD_FOLDER'], blank_filename))
		data.save(os.path.join(app.config['UPLOAD_FOLDER'], data_filename))
		layout.save(os.path.join(app.config['UPLOAD_FOLDER'], layout_filename))
		output, blanked_prism, normalized_prism = RunAnalysis(os.path.join(app.config['UPLOAD_FOLDER'], blank_filename), os.path.join(app.config['UPLOAD_FOLDER'], data_filename), os.path.join(app.config['UPLOAD_FOLDER'], layout_filename))
		normal = tb.Dataset().load(open(os.path.join(app.config['UPLOAD_FOLDER'], normalized_prism)).read())
		normal_prism = normal.html
		raw = tb.Dataset().load(open(os.path.join(app.config['UPLOAD_FOLDER'], blanked_prism)).read())
		raw_prism = raw.html
		return render_template('input_form.html', form=form, form2=form2, result=os.path.join(app.config['IMAGE_FOLDER'], output), normal_prism=normal_prism, raw_prism=raw_prism, raw_data=None)
		#redirect(url_for('uploaded_file', filename="figure.png"))
		#output
	return render_template('input_form.html', form=form, form2= form2, result=None, normal_prism=None, raw_prism=None, raw_data=None)

@app.route('/instructions', methods=['GET', 'POST'])
#@auth.login_required
def instructions():
	return render_template('instructions.html')

@app.route('/microplate/uploads/<filename>')
def uploaded_file(filename):
	return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def delete_files():
	for the_file in os.listdir(os.path.join(app.config['UPLOAD_FOLDER'])):
		file_path = os.path.join(app.config['UPLOAD_FOLDER'], the_file)
		try:
			if os.path.isfile(file_path):
				os.unlink(file_path)
			#elif os.path.isdir(file_path): shutil.rmtree(file_path) #remove subdirectory
		except Exception as e:
			print(e)

app.add_url_rule('/uploads/<filename>', 'uploaded_file', build_only=True)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
	'/uploads':  app.config['UPLOAD_FOLDER']
})

if __name__ == '__main__':
	app.run(debug = True)