from wtforms import StringField, validators, Form, FileField, SubmitField, MultipleFileField, HiddenField
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import DataRequired
from wtforms.widgets import html_params, HTMLString
import ntpath

class ButtonWidget(object):
	"""
	Renders a multi-line text area.
	`rows` and `cols` ought to be passed as keyword args when rendering.
	"""
	input_type = 'button'

	html_params = staticmethod(html_params)

	def __call__(self, field, **kwargs):
		kwargs.setdefault('id', field.id)
		kwargs.setdefault('type', self.input_type)
		if 'value' not in kwargs:
			kwargs['value'] = field._value()

		return HTMLString('<button {params}>{label}</button>'.format(
			params=self.html_params(name=field.name, onclick='pictureChange("' + field.name + '.png")', **kwargs),
			label=field.label.text)
		)


class ButtonField(StringField):
	widget = ButtonWidget()


def Form(arg):
	class TempForm(FlaskForm):
		attribute2 = HiddenField()
	for thing in arg:
		setattr(TempForm, thing, ButtonField(label=ntpath.basename(thing)))
	return TempForm()


class Index(FlaskForm):
	ec_button = SubmitField(label='EC Analysis')
	rodeostat_button = SubmitField(label='RodeoStat Analysis')
	microplate_button = SubmitField(label='Microplate Analysis')
	instructions_button = SubmitField(label='Instructions')

class EC(FlaskForm):
	data_file = MultipleFileField('Data File(s)')

class RodeoStat(FlaskForm):
	data_file = MultipleFileField('Data File(s)')

class InputForm(FlaskForm):
	blank_file = FileField(validators=[FileRequired(), FileAllowed(['txt'], 'Text files only')])
	data_file = FileField(validators=[FileRequired(), FileAllowed(['txt'], 'Text files only')])
	layout_file = FileField(validators=[FileRequired(), FileAllowed(['xls', 'xlsx'], 'Excel files only')])
	



'''
	name = StringField(
		label='Sample Name', default='C003A',
		validators=[validators.InputRequired()])
	cond = StringField(
		label='Conditions', default='[0][5][10]',
		validators=[validators.InputRequired()])
	unit = StringField(
		label='Units', default='ppb',
		validators=[validators.InputRequired()])
	wells = StringField(
		label='Wells', default='[A01, B01, C01], [A02, B02, C02], [A03, B03, C03]',
		validators=[validators.InputRequired()])
'''
'''
def form_generator(sample_num):

	class InputForm(Form):
		pass
	for sample in range(sample_num):
		name = StringField(
			label='Sample Name', default='C003A',
			validators=[validators.InputRequired()])
		cond = StringField(
			label='Conditions', default='[0][5][10]',
			validators=[validators.InputRequired()])
		unit = StringField(
			label='Units', default='ppb',
			validators=[validators.InputRequired()])
		wells = StringField(
			label='Wells', default='[A01, B01, C01], [A02, B02, C02], [A03, B03, C03]',
			validators=[validators.InputRequired()])
		setattr(InputForm, name, cond, unit, wells)
	return InputForm(request.form)
'''