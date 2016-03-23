from flask import request, Response, abort, redirect, flash
from flask_admin.contrib.mongoengine import ModelView
from flask_admin.contrib.mongoengine.helpers import format_error
from flask_admin.helpers import url_for
from flask_admin.model.helpers import get_mdict_item_or_list
from flask_admin import expose
from flask_babelex import gettext
from wtforms.validators import regexp

import mongoengine
from mongoengine.base.common import get_document
from mongoengine.context_managers import switch_db

import json

from bson import ObjectId

from .models import ContentSchema, available_fields
from .form.widgets import PredefinedSelect
from .form.form import CmfModelConverter
from .fields import MultilangField

import logging

log = logging.getLogger("flask-admin.mongo")

schema_arg = 'schema_id'

class ContentSchemaView(ModelView):
    form_args = {
        'name': {
            'validators': [regexp('^[a-zA-Z0-9_]+$')],
        }
    }

    form_subdocuments = {
        'schema_fields': {
            'form_subdocuments': {
                None: {
                    'form_args': {
                        'type': {
                            'widget': PredefinedSelect([(k, v['label']) for k, v in available_fields.items()])
                        }
                    }
                }
            }
        }
    }

class BaseSnapshotView:

    has_menu = True

    snapshot_model = None

    snapshots_template = 'admin/model/snapshots.html'

    def edit_menu(self):
        id = get_mdict_item_or_list(request.args, 'id')
        if id is None:
            return False

        def is_active(endpoint):
            return endpoint == request.url_rule.endpoint

        edit_menu = [{
            'url': url_for('.snapshots_view', id=id),
            'endpoint': self.endpoint+'.snapshots_view',
            'label': 'Snapshots',
            'is_active': is_active,
        }]

        return edit_menu

    def get_snapshot_model(self):
        if self.snapshot_model is None:
            return self.model.snapshot_model

        return self.snapshot_model

    @expose('/snapshots/')
    def snapshots_view(self):
        id = get_mdict_item_or_list(request.args, 'id')
        if id is None or not ObjectId.is_valid(id):
            abort(404)

        master = self.model.objects.get_or_404(id=id)
        snapshots = self.get_snapshot_model().objects(master=id).order_by('-created_at')

        return self.render(self.snapshots_template, model=master, snapshots=snapshots)

    @expose('/snapshots/<snapshot_id>/preview/<typ>')
    def preview_snapshot(self, snapshot_id, typ):
        snapshot = self.get_snapshot_model().objects.get_or_404(id=snapshot_id)
        if typ == 'json':
            return Response(snapshot.to_json(indent=4), mimetype="application/json")
        elif typ == 'html':
            # TODO: Create html preview template
            abort(404)

    @expose('/create-snapshot')
    def create_snapshot(self):
        id = get_mdict_item_or_list(request.args, 'id')
        if id is None or not ObjectId.is_valid(id):
            abort(404)

        master = self.model.objects.get_or_404(id=id)

        self.get_snapshot_model().objects(master=id, published=True).update(published=False)

        snapshot = master.create_snapshot()
        snapshot.published = True
        snapshot.save()

        return redirect(url_for('.snapshots_view', id=id))

    @expose('/delete-snapshot', methods=('POST',))
    def delete_snapshot(self):
        id = get_mdict_item_or_list(request.args, 'id')
        if id is None:
            abort(404)

        snapshot_id = self.object_id_converter(request.form['id'])
        self.get_snapshot_model().objects(id=snapshot_id).delete()

        return redirect(url_for('.snapshots_view', id=id))


class TextSearchMixin:

    def init_search(self):
        self._search_supported = True
        return True

    def _search(self, query, search_term):
        return query.search_text(search_term)



class BaseView(ModelView):

    model_form_converter = CmfModelConverter

    edit_template = 'admin/model/edit.html'

    allowed_search_types = (mongoengine.StringField,
                            mongoengine.URLField,
                            mongoengine.EmailField,
                            MultilangField)

    def __init__(self, model, **kwargs):
        super(BaseView, self).__init__(model, **kwargs)
        model.view_endpoint = self.endpoint

    @expose('/ajax/reference/<class_name>/<id>')
    def ajax_reference(self, class_name, id):
        oid = ObjectId(id)
        doc = get_document(class_name)
        obj = doc.objects.get(id=oid)

        return Response(json.dumps({
            'label': str(obj),
            'id': str(obj.id),
            'collection': obj.to_dbref().collection,
            'url': url_for(obj.view_endpoint + ".edit_view", id=obj.id)
        }), content_type='application/json')


class DbAwareView:

    def create_model(self, form):
        try:
            model = self.model()
            form.populate_obj(model)
            self._on_model_change(form, model, True)
            model.save()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to create record. %(error)s',
                              error=format_error(ex)),
                      'error')
                log.exception('Failed to create record.')

            return False
        else:
            self.after_model_change(form, model, True)

        return model


class BaseContentView(BaseView):
    schema_arg = schema_arg

    form_excluded_columns = ('created_at', 'updated_at', 'updated_by', 'created_by', 'schema')
    column_exclude_list = ('schema', 'updated_by', 'created_by')

    _schema = None

    def __init__(self, model, name=None,
                 category=None, endpoint=None, url=None, static_folder=None,
                 menu_class_name=None, menu_icon_type=None, menu_icon_value=None, schema=None):
        super(BaseContentView, self).__init__(model, name=name, category=category, endpoint=endpoint, url=url,
                                              static_folder=static_folder,
                                              menu_class_name=menu_class_name,
                                              menu_icon_type=menu_icon_type,
                                              menu_icon_value=menu_icon_value)

        self._schema = schema
        self._model = model

    @property
    def schema(self) -> ContentSchema:
        if isinstance(self._schema, ObjectId):
            self._schema = ContentSchema.objects.get(id=self._schema)
        if isinstance(self._schema, str):
            self._schema = ContentSchema.objects.get(name=self._schema)

        return self._schema

    @schema.setter
    def schema(self, val):
        self._schema = val

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, val):
        self._model = val

    def _handle_view(self, name, **kwargs):
        super(BaseContentView, self)._handle_view(name, **kwargs)

        if self.schema_arg in request.args:
            logging.debug('Found schema id {}'.format(request.args.get(self.schema_arg)))
            schema_id = request.args.get(self.schema_arg)
            if ObjectId.is_valid(schema_id):
                self._schema = ObjectId(request.args.get(self.schema_arg))
            else:
                self._schema = schema_id

        self._refresh_cache()

    @staticmethod
    def sub_menu():
        schemas = ContentSchema.objects()
        menu = []
        for schema in schemas:
            menu.append({
                'name': schema.label,
                'id': schema.id,
            })

        return menu

    def get_query(self):
        if self.schema is not None:
            return self.model.objects(schema=self.schema)
        else:
            return self.model.objects()

    def on_model_change(self, form, model, is_created):
        if is_created:
            if hasattr(model, 'schema_instance'):
                model.schema = model.schema_instance
            else:
                model.schema = self.schema

    def get_url(self, endpoint, **kwargs):
        if self.schema is not None and self.schema_arg not in kwargs:
            kwargs[self.schema_arg] = self.schema.id

        return super(BaseContentView, self).get_url(endpoint, **kwargs)

    def scaffold_form(self):
        if self.form_extra_fields is None:
            self.form_extra_fields = {}
        if self.schema is not None:
            for field in self.schema.schema_fields:
                form_class = available_fields[field.type]['form_class']
                self.form_extra_fields[field.name] = form_class()

        return super(BaseContentView, self).scaffold_form()

    def scaffold_list_columns(self):
        columns = []

        if self.schema is not None:
            for field in self.schema.schema_fields:
                if field.show_in_list is True:
                    columns.append(field.name)

        return columns + super(BaseContentView, self).scaffold_list_columns()
