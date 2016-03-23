from mongoengine.base import BaseField
from mongoengine.fields import DynamicField
from babel import Locale
from flask_babelex import get_locale

default_locale = Locale('en', 'US')

class TranslationsDict(dict):

    def __new__(cls, default: [str, None], translations=None):
        self = {}

        if isinstance(translations, dict):
            for k, v in translations.items():
                self[k] = v
        if default is not None:
            self["default"] = default

        return self

class MultilangString:

    def __init__(self, translations: [None, TranslationsDict], locale=default_locale):
        self.translations = translations
        self._locale = locale

    @property
    def locale(self) -> Locale:
        locale = get_locale()
        if locale is None:
            return self._locale
        return locale

    @locale.setter
    def locale(self, locale: Locale):
        self._locale = locale

    def __str__(self):
        locale = self.locale
        locale_str = str(locale)
        if self.translations is None or len(self.translations) == 0:
            return ""
        if locale_str in self.translations:
            return self.translations[locale_str]
        elif 'default' in self.translations:
            return self.translations["default"]
        else:
            return list(self.translations.values())[0]

    def __iter__(self):
        for k, v in self.translations.items():
            yield (k, v)

    def to_mongo(self):
        return self.translations

class MultilangField(DynamicField):

    def __init__(self, max_length=None, **kwargs):
        self.max_length = max_length
        super(MultilangField, self).__init__(**kwargs)

    def to_mongo(self, value: MultilangString):
        if isinstance(value, MultilangString):
            return value.translations
        elif isinstance(value, dict):
            return value

        raise ValueError("Must be dict or MultilangString")

    def to_python(self, value):
        return MultilangString(TranslationsDict(None, translations=value))

    def __set__(self, instance, value: [MultilangString, str]):
        if isinstance(value, str):
            translations = TranslationsDict(value)
            value = MultilangString(translations)

        super().__set__(instance, value)





