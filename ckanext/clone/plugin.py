import ckan.plugins as plugins


class ClonePlugin(plugins.SingletonPlugin):
    """
    Setup plugin
    """
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IConfigurer, inherit=True)
    
    def before_map(self, map):

        map.connect('clone', '/clone',
            controller='ckanext.clone.controller:CloneController',
            action='bad_url')

        map.connect('clone', '/clone/{id}',
            controller='ckanext.clone.controller:CloneController',
            action='index')

        return map
    
    def update_config(self, config):
        plugins.toolkit.add_template_directory(config, 'templates')