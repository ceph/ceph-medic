"""
JSON Loading utilities
"""
import os
import imp


def load_config(filepath, **kw):
    '''
    Creates a configuration dictionary from a file.

    :param filepath: The path to the file.
    '''

    abspath = os.path.abspath(os.path.expanduser(filepath))
    conf_dict = {}
    if not os.path.isfile(abspath):
        raise RuntimeError('`%s` is not a file.' % abspath)

    # First, make sure the code will actually compile (and has no SyntaxErrors)
    with open(abspath, 'rb') as f:
        compiled = compile(f.read(), abspath, 'exec')

    # Next, attempt to actually import the file as a module.
    # This provides more verbose import-related error reporting than exec()
    absname, _ = os.path.splitext(abspath)
    basepath, module_name = absname.rsplit(os.sep, 1)
    try:
        imp.load_module(
            module_name,
            *imp.find_module(module_name, [basepath])
        )
    except ImportError:
        pass

    # If we were able to import as a module, actually exec the compiled code
    exec(compiled, globals(), conf_dict)
    conf_dict['__file__'] = abspath
    return conf_dict
