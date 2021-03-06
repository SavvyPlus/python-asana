import json
import string
import os

PACKAGE_NAME = 'asana'

GENERATED_WARNING = '# This file is automatically generated by generate.py using api.json\n'

RESOURCES_INIT_PY_TEMPLATE = string.Template('''
from . import $resource_names
''')

RESOURCE_CLASS_TEMPLATE = string.Template('''
from .$module_name_base import $class_name_base

class $name($class_name_base):
    pass
''')

RESOURCE_BASE_CLASS_TEMPLATE = string.Template('''
class $name:
    def __init__(self, client=None):
        self.client = client
''')

RESOURCE_METHOD_TEMPLATE = string.Template('''
    def $name(self, params={}, **options):$doc_string$options
        return self.client.$method('$url', params, **options)
''')

RESOURCE_METHOD_TEMPLATE_WITH_ARGS = string.Template('''
    def $name(self, $args, params={}, **options):$doc_string$options
        path = '$url' % ($args)
        return self.client.$method(path, params, **options)
''')

api = json.loads(open('api.json', 'r').read())
docs = json.loads(open('docs.json', 'r').read())

resource_names = []
for resource_name, resource in api['resources'].iteritems():
    resource_names.append(resource_name)
    method_docs = docs['resources'][resource_name]['methods']

    class_name = resource_name.capitalize()
    module_name = resource_name.lower()
    class_name_base = '_' + resource_name.capitalize()
    module_name_base = 'gen/' + resource_name.lower()

    resource_base_py = open(PACKAGE_NAME + '/resources/' + module_name_base + '.py', 'w')
    resource_base_py.write(GENERATED_WARNING)
    resource_base_py.write(RESOURCE_BASE_CLASS_TEMPLATE.substitute(name=class_name_base))
    if 'methods' in resource:
        for method_name, method in resource['methods'].iteritems():
            template_vars = {
                'name': method_name,
                'method': method['method'],
                'url': method['url'],
                'args': ', '.join(method['args']) if 'args' in method and len(method['args']) > 0 else None,
                'options': '\n        options = self.client._merge_options(' + repr(method['dispatch_options']) + ')' if 'dispatch_options' in method else '',
                'doc_string': '\n        """' + method_docs[method_name]['doc'] + '"""' if method_name in method_docs else ''
            }

            if method.get('collection', False):
                if method['method'] != 'get':
                    raise Exception('"collection" set to true with "method" other than "get" is not supported')
                template_vars['method'] = 'get_collection'

            if template_vars['args'] is None:
                resource_base_py.write(RESOURCE_METHOD_TEMPLATE.substitute(**template_vars))
            else:
                resource_base_py.write(RESOURCE_METHOD_TEMPLATE_WITH_ARGS.substitute(**template_vars))

    resource_base_py.close()

    if not os.path.exists(PACKAGE_NAME + '/resources/' + module_name + '.py'):
        resource_py = open(PACKAGE_NAME + '/resources/' + module_name + '.py', 'w')
        resource_py.write(RESOURCE_CLASS_TEMPLATE.substitute(
            name=class_name,
            class_name_base=class_name_base,
            module_name_base=module_name_base.replace("/",".")
        ))
        resource_py.close()

resource_names.sort()

init_py = open(PACKAGE_NAME + '/resources/__init__.py', 'w')
init_py.write(GENERATED_WARNING)
init_py.write(RESOURCES_INIT_PY_TEMPLATE.substitute(resource_names=', '.join(resource_names)))
init_py.close()

init_py = open(PACKAGE_NAME + '/resources/gen/__init__.py', 'w')
init_py.write(GENERATED_WARNING)
# init_py.write(RESOURCES_INIT_PY_TEMPLATE.substitute(resource_names=', '.join(resource_names)))
init_py.close()
