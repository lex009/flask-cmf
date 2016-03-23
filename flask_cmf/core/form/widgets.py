from wtforms.widgets import HTMLString, html_params, Select
from flask_babelex import gettext


class PredefinedSelect(Select):

    _options = []

    def __init__(self, options):
        self.options = options
        super(PredefinedSelect, self).__init__()

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, options):
        self._options = options

    def __call__(self, field, **kwargs) -> HTMLString:
        kwargs.setdefault('id', field.id)
        html = ['<select %s>' % html_params(name=field.name, **kwargs)]
        for val, label in self.options:
            selected = False
            if val == field.data:
                selected = True
            html.append(self.render_option(val, label, selected))
        html.append('</select>')

        return HTMLString(''.join(html))


class ReferenceWidget:

    @staticmethod
    def single_reference(field, html, extra_rows=None):
        if extra_rows is None:
            extra_rows = []

        html.append('<td>')

        if field.data['id'] is not None:
            html.append('<span class="cmf-reference-label"><a href="">' + str(field.object_data) + '</a></span>')
        else:
            html.append('<span class="cmf-reference-label"></span>')

        html.append('</td>')

        html.append('<td>')

        choose_class = ''
        if field.data['id'] is not None:
            choose_class = 'hidden'
        html.append('<a class="btn btn-default cmf-reference-link ' + choose_class + '" href="#">' + gettext("Choose") + '</a>')

        html.append(field['id'](class_='cmf-reference-id'))
        html.append(field['class_name'](class_='cmf-reference-classname'))
        html.append(field['database'](class_='cmf-reference-database'))

        unset_class = ''
        if field.data['id'] is None:
            unset_class = 'hidden'
        html.append('<a class="btn btn-danger ' + unset_class + ' cmf-reference-clear-link" href="#">' +
                    gettext("Clear") + '</a>')
        html.append('</td>')

        for row in extra_rows:
            html.append(row)

    def __call__(self, field, **kwargs) -> HTMLString:
        html = ['<table class="table">']
        html.append('<tr>')
        self.single_reference(field, html)
        html.append('</tr>')
        html.append('</table>')

        return HTMLString(''.join(html))

class DynamicListWidget(object):

    @staticmethod
    def add_btn() -> str:
        return '<button type="button" role="button" class="btn btn-default cmf-list-form-add-btn">' \
               '<i class="fa fa-fw fa-plus-square"></i> ' + gettext('Add translation') + '</button>'

    @staticmethod
    def delete_btn() -> str:
        return '<button type="button" role="button" class="btn btn-danger cmf-list-form-remove-btn">' \
               '<i class="fa fa-fw fa-remove"></i></button>'

class TranslationWidget(object):

    def __call__(self, fields, **kwargs) -> str:
        if kwargs.get('template', False) is True:
            html = ['<div class="input-group cmf-list-form-template">']
        else:
            html = ['<div class="input-group cmf-list-form-item">']

        html.append('<div class="input-group-addon">')
        html.append(fields['locale'](class_='cmf-list-form-control'))
        html.append('</div>')
        html.append(fields['text'](class_='cmf-list-form-control form-control'))
        html.append('<span class="input-group-btn">')
        html.append(DynamicListWidget.delete_btn())
        html.append('</span>')
        html.append('</div>')

        return HTMLString(''.join(html))

class MultilangWidget(DynamicListWidget):

    class_name = 'cmf-list-form-container cmf-multilang-container'

    def __init__(self):
            self.html_tag = 'div'

    def __call__(self, field, **kwargs) -> str:
        kwargs.setdefault('id', field.id)
        kwargs['class'] = kwargs.get('class', '') + ' ' + self.class_name
        html = ['<%s %s>' % (self.html_tag, html_params(**kwargs))]
        html.append('<div class="cmf-list-fields-container">')
        for subfield in field:
            html.append('%s' % subfield())
        html.append('</div>')
        html.append('<input class="cmf-list-form-item-template" type="hidden" value=\'%s\'>' % field.template()())
        html.append(self.add_btn())
        html.append('</%s>' % self.html_tag)
        return HTMLString(''.join(html))
