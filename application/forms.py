from wtforms import StringField, PasswordField, SubmitField, BooleanField, DateField, validators, RadioField, SelectField, FieldList, FormField, SelectMultipleField
from flask_wtf import FlaskForm, Form
from wtforms.validators import InputRequired

class Spot_SearchForm(FlaskForm):
    category = SelectMultipleField('What are you searching for?', choices=['any', 'artist', 'album', 'track', 'playlist', 'show', 'episode'])
    search_term = StringField('Search Term', filters = [lambda x: x or None])
    how_many = StringField('How many results?',filters = [lambda x: x or None])
    artist = StringField('Constrain Artist',filters = [lambda x: x or None])
    album = StringField('Constrain Album',filters = [lambda x: x or None])
    track = StringField('Constrain Track',filters = [lambda x: x or None])
    release_date = StringField('Constrain Release Date or Range',filters = [lambda x: x or None])
    only_new = BooleanField('Limit to last 2 weeks?')
    submit = SubmitField('Search')

class ArtistTracksForm(FlaskForm):
    artist = StringField('Who are you searching for?')
    submit = SubmitField('search')

class ArtistForm(FlaskForm):
    artist = BooleanField()
    submit = SubmitField('GO DO STUFF')

class ResultsForm(FlaskForm):
    artists = FieldList(FormField(ArtistForm), min_entries=1)
    original = BooleanField("Only include tracks from artist's own releases?")
    include_comp = BooleanField("Include tracks from compilation albums? (not poss if only own releases")
    submit = SubmitField('GO')

class TracklistForm(FlaskForm):
    track = StringField()
    submit = SubmitField('FUCKIN AYE')








'''
class ImageForm(FlaskForm):
    frequency = SelectField(choices=[('monthly', 'Monthly'),('weekly', 'Weekly')])
    caption = StringField('Caption')
    credit = StringField('Credit')

class TestForm(FlaskForm):
    images = FieldList(FormField(ImageForm), min_entries=10)


'''






# class ChoicesForm(FlaskForm):
#     artist_dict =
#     image = FileField('Upload')
#     caption = StringField('Caption')
#     credit = StringField('Credit')
#
# class MyForm(FlaskForm):
#     images = FieldList(FormField(ImageForm), min_entries=10)








'''

    class wtforms.fields.RadioField(default field arguments, choices=[], coerce=unicode)[source]

        Like a SelectField, except displays a list of radio buttons.

        Iterating the field will produce subfields (each containing a label as well) in order to allow custom rendering of the individual radio fields.

        {% for subfield in form.radio %}
            <tr>
                <td>{{ subfield }}</td>
                <td>{{ subfield.label }}</td>
            </tr>
        {% endfor %}

        Simply outputting the field without iterating its subfields will result in a <ul> list of radio choices.

    '''