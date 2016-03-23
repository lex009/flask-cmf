from flask_admin.menu import MenuView
from flask import has_request_context, request

class CmsMenuView(MenuView):

    url_kwargs = {}

    def __init__(self, name, view=None, url_kwargs=None, children_func=None):

        super(CmsMenuView, self).__init__(name, view)

        if children_func is not None:
            if not callable(children_func):
                raise AttributeError("Children function must be callable")
            self.children_func = children_func

        if url_kwargs is not None:
            self.url_kwargs = url_kwargs

    def is_active(self, view):
        if has_request_context() and hasattr(view, 'schema_arg') and view.schema_arg in request.args:
            schema_id = request.args[view.schema_arg]
            if view.schema_arg in self.url_kwargs and str(self.url_kwargs[view.schema_arg]) == schema_id:
                return True
            else:
                return False

        return super(CmsMenuView, self).is_active(view)

    def get_url(self):
        return self._view.get_url('%s.%s' % (self._view.endpoint, self._view._default_view), **self.url_kwargs)

    def build_children(self):
        if hasattr(self, 'children_func'):
            for item in self.children_func():
                self.add_child(CmsMenuView(item['name'], self._view, {self._view.schema_arg: item['id']}))

