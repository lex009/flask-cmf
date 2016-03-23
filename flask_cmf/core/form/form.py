from flask_admin.contrib.mongoengine.form import CustomModelConverter as ModelConverter
from flask_mongoengine.wtf import orm

from .fields import MultilangField, GenericReferenceField


class CmfModelConverter(ModelConverter):

    def __init__(self, view):
        super(CmfModelConverter, self).__init__(view)

    @orm.converts('MultilangField')
    def conv_Multilang(self, model, field, kwargs):

        kwargs = {}
        if field.required:
            kwargs['min_entries'] = 1
        if field.max_length:
            kwargs['text_type'] = 'text'
        else:
            kwargs['text_type'] = 'textarea'

        return MultilangField(**kwargs)

    @orm.converts('GenericReferenceField')
    def conv_GenericReference(self, model, field, kwargs):
        edit_url = None
        if hasattr(model, 'view_endpoint'):
            edit_url = model.view_endpoint+'.edit_view'
        return GenericReferenceField(edit_url=edit_url)
