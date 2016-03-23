from wtforms.fields import FieldList, StringField, SelectField, FormField, TextAreaField
from wtforms.widgets import HiddenInput
from wtforms.utils import unset_value
from wtforms import Form

from bson import ObjectId

from mongoengine.base.common import get_document

from .widgets import TranslationWidget, MultilangWidget, ReferenceWidget, PredefinedSelect
from flask_cmf.core.fields import MultilangString


locales_list = [
    ("default", "default"),
    ("ru_RU", "ru_RU"),
    ("en_RU", "en_RU"),
]

# class PredefinedSelectField(SelectField):
#
#
#     def __init__(self, options, *args, **kwargs):
#         super(PredefinedSelectField, self).__init__(*args, **kwargs)

class DynamicListField(FieldList):

    def template(self) -> str:
        name = '%s-*' % self.short_name
        id = '%s-*' % self.id

        field = self.unbound_field.bind(form=None, name=name, prefix=self._prefix, id=id, _meta=self.meta)
        field.process(None)

        return field


class MultilangField(DynamicListField):

    widget = MultilangWidget()

    def __init__(self, text_type='textarea', **kwargs):
        if text_type not in ['text', 'textarea']:
            raise ValueError('text_type must be text or textarea')
        self.text_type = text_type
        translation_form = self.get_translation_form()
        unbound = FormField(translation_form, widget=TranslationWidget())
        super().__init__(unbound, **kwargs)

    def get_translation_form(self):
        class TranslationForm(Form):
            locale = SelectField(choices=locales_list)

        if self.text_type == 'text':
            setattr(TranslationForm, 'text', StringField())
        elif self.text_type == 'textarea':
            setattr(TranslationForm, 'text', TextAreaField())

        return TranslationForm

    def populate_obj(self, obj, name):
        translations = {}
        if len(self.data) == 1:
            translations['default'] = self.data[0]['text']
        else:
            for locale_data in self.data:
                translations[locale_data['locale']] = locale_data['text']
        string = MultilangString(translations)
        setattr(obj, name, string)

    def process(self, formdata, data=unset_value):
        self.entries = []
        if data is unset_value or not data:
            try:
                data = self.default()
            except TypeError:
                data = self.default

        self.object_data = data

        if formdata:
            indices = sorted(set(self._extract_indices(self.name, formdata)))
            if self.max_entries:
                indices = indices[:self.max_entries]

            idata = iter(data)
            for index in indices:
                try:
                    obj_data = next(idata)
                except StopIteration:
                    obj_data = unset_value
                self._add_entry(formdata, obj_data, index=index)
        else:
            if data is unset_value or not data:
                self._add_entry(formdata, self.default)
            if isinstance(data, str):
                obj_data = {
                    'locale': 'default',
                    'text': data,
                }
                self._add_entry(formdata, obj_data)
            else:
                items = {}
                if isinstance(data, dict):
                    items = data
                elif isinstance(data, MultilangString):
                    items = data.translations

                for k, v in items.items():
                    obj_data = {
                        'locale': k,
                        'text': v,
                    }
                    self._add_entry(formdata, obj_data)

        while len(self.entries) < self.min_entries:
            self._add_entry(formdata)

class GenericReferenceForm(Form):

    id = StringField(widget=HiddenInput())
    class_name = StringField(widget=HiddenInput())
    database = StringField(widget=HiddenInput())


class GenericReferenceField(FormField):

    widget = ReferenceWidget()

    def __init__(self, label=None, validators=None, separator='-', **kwargs):
        if 'edit_url' in kwargs:
            self.edit_url = kwargs['edit_url']
            del kwargs['edit_url']

        super(GenericReferenceField, self).__init__(GenericReferenceForm, label, validators, separator, **kwargs)

    def populate_obj(self, obj, name):
        candidate = getattr(obj, name, None)
        if candidate is None and self.data['class_name'] != '':
            class_ = get_document(self.data['class_name'])
            candidate = class_(pk=ObjectId(self.data['id']))
        if self.data['id'] == '':
            candidate = None

        setattr(obj, name, candidate)
