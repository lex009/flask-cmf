from wtforms import fields as form_fields

from mongoengine import DynamicDocument, Document, EmbeddedDocument, signals, DynamicEmbeddedDocument, CASCADE
from mongoengine.fields import DateTimeField, StringField, BooleanField, ListField, \
    EmbeddedDocumentField, ReferenceField, IntField, GenericReferenceField
from mongoengine.document import TopLevelDocumentMetaclass

from flask_mongoengine import BaseQuerySet

from .form.fields import MultilangField
from .fields import MultilangField as MongoMultilangField

from datetime import datetime

import logging

available_fields = {
    'text': {
        'form_class': form_fields.StringField,
        'mongo_class': StringField,
        'label': 'Text'
    },
    'multilang': {
        'form_class': MultilangField,
        'mongo_class': MongoMultilangField,
        'label': 'Multi language'
    },
    'int': {
        'form_class': form_fields.IntegerField,
        'mongo_class': IntField,
        'label': 'Integer'
    },
}

schema_instances = []

def register_custom_field(name: str, info: dict):
    available_fields[name] = info

def update_schemas():
    for schema in schema_instances:
        logging.debug('Updating predefined schema {}'.format(schema.name))
        schema.save()


class SchemaBasedClass(TopLevelDocumentMetaclass):

    def __new__(mcs, name, bases, attrs):
        cls = super(SchemaBasedClass, mcs).__new__(mcs, name, bases, attrs)
        if 'schema_instance' in attrs:
            schema_instance = attrs['schema_instance']
            assert isinstance(schema_instance, ContentSchema)
            schema_instances.append(schema_instance)

        return cls


class AbstractContent(DynamicDocument, metaclass=SchemaBasedClass):
    """
    Base class for content
    """

    schema = ReferenceField('ContentSchema')

    created_at = DateTimeField(required=True, default=datetime.utcnow)

    updated_at = DateTimeField()

    created_by = GenericReferenceField()

    updated_by = GenericReferenceField()

    parent = GenericReferenceField()

    snapshot_exclude = ['schema']

    meta = {
        'abstract': True,
        'indexes': [
            {
                'fields': ['schema']
            },

            {
                'fields': ['schema', 'parent']
            }
        ],
        'queryset_class': BaseQuerySet,
    }

    @staticmethod
    def pre_save(sender, document, **kwargs):
        if hasattr(document, 'updated_at'):
            document.updated_at = datetime.now()
        if hasattr(document, 'schema_instance') and document.schema is None:
            document.schema = document.schema_instance

    def __str__(self) -> str:
        try:
            if hasattr(self, 'title'):
                title = getattr(self, 'title')
                if isinstance(title, dict):
                    return title['default']
                elif isinstance(title, str):
                    return title
                elif isinstance(title, object):
                    return str(title)
        except (KeyError, ):
            pass

        return str(self.id)

    def __setattr__(self, name: str, value):
        if not hasattr(self, name) and not name.startswith('_') and name != 'schema' and self.schema is not None:
            for custom_field in self.schema.schema_fields:
                if custom_field.name == name:
                    field_class = available_fields[custom_field.type]['mongo_class']
                    field = field_class(db_field=name)
                    field.name = name

                    self._dynamic_fields[name] = field
                    self._fields_ordered += (name,)
                    self._data[name] = value

                    value = field.to_python(value)

                    if hasattr(self, '_changed_fields'):
                        self._mark_as_changed(name)

                    self._dynamic_lock = True

        super(DynamicDocument, self).__setattr__(name, value)

signals.pre_save.connect(AbstractContent.pre_save)

class BaseContent(AbstractContent):

    meta = {
        'collection': 'base_content',
    }

class ContentField(EmbeddedDocument):

    name = StringField(required=True, max_length=100, min_length=3)

    type = StringField(required=True)

    searchable = BooleanField()

    show_in_list = BooleanField()


class ContentSchema(Document):

    name = StringField(max_length=100, min_length=3, primary_key=True, regex='^[a-zA-Z_\-]+$')

    label = StringField(required=True, max_length=100, min_length=3)

    schema_fields = ListField(EmbeddedDocumentField(ContentField))

    def __str__(self):
        return self.name


class Embeddable:

    def embed(self):
        d = DynamicEmbeddedDocument()
        if not hasattr(self, 'to_embed'):
            for prop, value in self._fields.items():
                setattr(d, prop, getattr(self, prop))
        else:
            for k in self.to_embed:
                d[k] = getattr(self, k)

        return d


class Snapshotable:

    snapshot_model = None

    snapshot_exclude = []

    def _create_snapshot_model(self):

        master_collection = self._collection.name
        collection = master_collection + '_snapshot'

        class Snapshot(DynamicDocument):
            meta = {
                'collection': collection
            }

            master = ReferenceField(self.__class__, reverse_delete_rule=CASCADE)

        return Snapshot

    def _fill_snapshot(self):
        snapshot = self.snapshot_model()
        snapshot.master = self
        for field, cls in self._fields.items():
            if field in self.snapshot_exclude or field == 'id' or field.startswith('_'):
                continue

            if isinstance(cls, ListField):
                items = []
                for item in getattr(self, field):
                    if hasattr(item, 'embed'):
                        items.append(item.embed())
                    else:
                        items.append(item)
                if len(items) > 0:
                    setattr(snapshot, field, items)
            elif isinstance(cls, GenericReferenceField) or isinstance(cls, ReferenceField):
                item = getattr(self, field)
                if hasattr(item, 'embed'):
                    setattr(snapshot, field, item.embed())
                else:
                    setattr(snapshot, field, item)
            else:
                setattr(snapshot, field, getattr(self, field))

        snapshot.created_at = datetime.now()
        if hasattr(self, 'created_at'):
            snapshot.master_created_at = self.created_at

        return snapshot

    def create_snapshot(self):
        if self.snapshot_model is None:
            self.snapshot_model = self._create_snapshot_model()

        snapshot = self._fill_snapshot()

        return snapshot


