from flask_admin import Admin
from .menu import CmsMenuView

class CmsAdmin(Admin):

    def menu(self):
        self._refresh_menu_children()
        return super(CmsAdmin, self).menu()

    def _refresh_menu_children(self):
        for menu in self._menu:
            if hasattr(menu, 'build_children'):
                menu.build_children()

    def _add_view_to_menu(self, view):
        if hasattr(view, 'sub_menu'):
            menu_view = CmsMenuView(view.name, view, children_func=view.sub_menu)
            menu_view.build_children()
        else:
            menu_view = CmsMenuView(view.name, view)

        self._add_menu_item(menu_view, view.category)


class ReferenceAdmin(CmsAdmin):

    endpoint_prefix = 'ref-'

    base_template = 'reference_admin/base.html'

    def add_view(self, view):
        view.endpoint = self.endpoint_prefix + view.endpoint
        super(ReferenceAdmin, self).add_view(view)

def create_reference_admin(app, url='/reference-admin'):
    return CmsAdmin(
        app,
        name='Reference',
        endpoint='template',
        base_template='reference_admin/base.html',
        url=url
    )
