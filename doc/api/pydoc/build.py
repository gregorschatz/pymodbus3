"""
Pydoc sub-class for generating documentation for entire packages.

Taken from: http://pyopengl.sourceforge.net/pydoc/OpenGLContext.pydoc.pydoc2.html
Author: Mike Fletcher
"""
import logging
import pydoc
import inspect
import shutil
import sys
import os

_log = logging.getLogger(__name__)


def classify_class_attrs(cls):
    """Return list of attribute-descriptor tuples.

    For each name in dir(cls), the return list contains a 4-tuple
    with these elements:

        0. The name (a string).

        1. The kind of attribute this is, one of these strings:
               'class method'    created via classmethod()
               'static method'   created via staticmethod()
               'property'        created via property()
               'method'          any other flavor of method
               'data'            not a method

        2. The class which defined this attribute (a class).

        3. The object as obtained directly from the defining class's
           __dict__, not via getattr.  This is especially important for
           data attributes:  C.data is just a data object, but
           C.__dict__['data'] may be a data descriptor with additional
           info, like a __doc__ string.
    
    Note: This version is patched to work with Zope Interface-bearing objects
    """

    mro = inspect.getmro(cls)
    names = dir(cls)
    result = []
    for name in names:
        # Get the object associated with the name.
        # Getting an obj from the __dict__ sometimes reveals more than
        # using getattr.  Static and class methods are dramatic examples.
        if name in cls.__dict__:
            obj = cls.__dict__[name]
        else:
            try:
                obj = getattr(cls, name)
            except AttributeError:
                continue

        # Figure out where it was defined.
        home_cls = getattr(obj, "__objclass__", None)
        if home_cls is None:
            # search the dicts.
            for base in mro:
                if name in base.__dict__:
                    home_cls = base
                    break

        # Get the object again, in order to get it from the defining
        # __dict__ instead of via getattr (if possible).
        if home_cls is not None and name in home_cls.__dict__:
            obj = home_cls.__dict__[name]

        # Also get the object via getattr.
        obj_via_getattr = getattr(cls, name)

        # Classify the object.
        if isinstance(obj, staticmethod):
            kind = "static method"
        elif isinstance(obj, classmethod):
            kind = "class method"
        elif isinstance(obj, property):
            kind = "property"
        elif (inspect.ismethod(obj_via_getattr) or
              inspect.ismethoddescriptor(obj_via_getattr)):
            kind = "method"
        else:
            kind = "data"

        result.append((name, kind, home_cls, obj))

    return result
inspect.classify_class_attrs = classify_class_attrs


class DefaultFormatter(pydoc.HTMLDoc):
    def docmodule(self, obj, name=None, mod=None, package_context=None, *ignored):
        """Produce HTML documentation for a module object."""
        name = obj.__name__  # ignore the passed-in name
        parts = name.split('.')
        links = []
        for i in range(len(parts)-1):
            links.append(
                '<a href="%s.html"><font color="#ffffff">%s</font></a>' %
                ('.'.join(parts[:i+1]), parts[i]))
        linked_name = '.'.join(links + parts[-1:])
        head = '<big><big><strong>{0}</strong></big></big>'.format(linked_name)
        try:
            path = inspect.getabsfile(obj)
            url = path
            if sys.platform == 'win32':
                import nturl2path
                url = nturl2path.pathname2url(path)
            fake_link = '<a href="file:{0}">{1}</a>'.format(url, path)
        except TypeError:
            fake_link = '(built-in)'
        info = []
        if hasattr(obj, '__version__'):
            version = str(obj.__version__)
            if version[:11] == '$' + 'Revision: ' and version[-1:] == '$':
                version = version[11:-1].strip()
            info.append('version %s' % self.escape(version))
        if hasattr(obj, '__date__'):
            info.append(self.escape(str(obj.__date__)))
        if info:
            head += ' ({0})'.format(', '.join(info))
        result = self.heading(
            head, '#ffffff', '#7799ee', '<a href=".">index</a><br>' + fake_link)

        modules = inspect.getmembers(obj, inspect.ismodule)

        classes, cdict = [], {}
        for key, value in inspect.getmembers(obj, inspect.isclass):
            if (inspect.getmodule(value) or obj) is obj:
                classes.append((key, value))
                cdict[key] = cdict[value] = '#' + key
        for key, value in classes:
            for base in value.__bases__:
                key, modname = base.__name__, base.__module__
                module = sys.modules.get(modname)
                if modname != name and module and hasattr(module, key):
                    if getattr(module, key) is base:
                        if key not in cdict:
                            cdict[key] = cdict[base] = modname + '.html#' + key
        funcs, fdict = [], {}
        for key, value in inspect.getmembers(obj, inspect.isroutine):
            if inspect.isbuiltin(value) or inspect.getmodule(value) is obj:
                funcs.append((key, value))
                fdict[key] = '#-' + key
                if inspect.isfunction(value):
                    fdict[value] = fdict[key]
        data = []
        for key, value in inspect.getmembers(obj, pydoc.isdata):
            if key not in ['__builtins__', '__doc__']:
                data.append((key, value))

        doc = self.markup(pydoc.getdoc(obj), self.preformat, fdict, cdict)
        doc = doc and '<tt>%s</tt>' % doc
        result += '<p>{0}</p>\n'.format(doc)

        package_context.clean(classes, obj)
        package_context.clean(funcs, obj)
        package_context.clean(data, obj)
        
        if hasattr(obj, '__path__'):
            modpkgs = []
            modnames = []
            for file in os.listdir(obj.__path__[0]):
                path = os.path.join(obj.__path__[0], file)
                modname = inspect.getmodulename(file)
                if modname and modname not in modnames:
                    modpkgs.append((modname, name, 0, 0))
                    modnames.append(modname)
                elif pydoc.ispackage(path):
                    modpkgs.append((file, name, 1, 0))
            modpkgs.sort()
            contents = self.multicolumn(modpkgs, self.modpkglink)
            ## result = result + self.bigsection(
            ## 'Package Contents', '#ffffff', '#aa55cc', contents)
            result = result + self.module_section(obj, package_context)
        elif modules:
            contents = self.multicolumn(
                modules,
                lambda a: self.modulelink(a[1])
            )
            result = result + self.bigsection(
                'Modules', '#fffff', '#aa55cc', contents)

        if classes:
            class_list = map(lambda a: a[1], classes)
            contents = [
                self.formattree(inspect.getclasstree(class_list, 1), name)]
            for key, value in classes:
                contents.append(self.document(value, key, name, fdict, cdict))
            result = result + self.bigsection(
                'Classes', '#ffffff', '#ee77aa', ''.join(contents)
            )
        if funcs:
            contents = []
            for key, value in funcs:
                contents.append(self.document(value, key, name, fdict, cdict))
            result = result + self.bigsection(
                'Functions', '#ffffff', '#eeaa77', ''.join(contents)
            )
        if data:
            contents = []
            for key, value in data:
                try:
                    contents.append(self.document(value, key))
                except Exception:
                    pass
            result = result + self.bigsection(
                'Data', '#ffffff', '#55aa55', '<br>\n'.join(contents)
            )
        if hasattr(obj, '__author__'):
            contents = self.markup(str(obj.__author__), self.preformat)
            result = result + self.bigsection(
                'Author', '#ffffff', '#7799ee', contents)
        if hasattr(obj, '__credits__'):
            contents = self.markup(str(obj.__credits__), self.preformat)
            result = result + self.bigsection(
                'Credits', '#ffffff', '#7799ee', contents)

        return result

    def classlink(self, obj, modname):
        """Make a link for a class."""
        name, module = obj.__name__, sys.modules.get(obj.__module__)
        if hasattr(module, name) and getattr(module, name) is obj:
            return '<a href="{0}.html#{1}">{2}</a>'.format(
                module.__name__, name, name
            )
        return pydoc.classname(obj, modname)
    
    def module_section(self, obj, package_context ):
        """Create a module-links section for the given object (module)"""
        modules = inspect.getmembers(obj, inspect.ismodule)
        package_context.clean(modules, obj)
        package_context.recurse_scan(modules)

        if hasattr(obj, '__path__'):
            modpkgs = []
            modnames = []
            for file in os.listdir(obj.__path__[0]):
                path = os.path.join(obj.__path__[0], file)
                modname = inspect.getmodulename(file)
                if modname and modname not in modnames:
                    modpkgs.append((modname, obj.__name__, 0, 0))
                    modnames.append(modname)
                elif pydoc.ispackage(path):
                    modpkgs.append((file, obj.__name__, 1, 0))
            modpkgs.sort()
            # do more recursion here...
            for (modname, name, ya, yo) in modpkgs:
                package_context.add_interesting('.'.join((obj.__name__, modname)))
            items = []
            for (modname, name, ispackage, is_shadowed) in modpkgs:
                try:
                    # get the actual module obj...
                    #if modname == "events":
                    #    import pdb
                    #    pdb.set_trace()
                    module = pydoc.safeimport('{0}.{1}'.format(name, modname))
                    description, documentation = pydoc.splitdoc(inspect.getdoc(module))
                    if description:
                        items.append(
                            '{0} -- {1}'.format(
                                self.modpkglink((modname, name, ispackage, is_shadowed)),
                                description,
                            )
                        )
                    else:
                        items.append(
                            self.modpkglink((modname, name, ispackage, is_shadowed))
                        )
                except:
                    items.append(
                        self.modpkglink((modname, name, ispackage, is_shadowed))
                    )
            contents = '<br>'.join(items)
            result = self.bigsection(
                'Package Contents', '#ffffff', '#aa55cc', contents)
        elif modules:
            contents = self.multicolumn(
                modules,
                lambda a: self.modulelink(a[1])
            )
            result = self.bigsection(
                'Modules', '#fffff', '#aa55cc', contents)
        else:
            result = ""
        return result


class AlreadyDone(Exception):
    pass


class PackageDocumentationGenerator:
    """A package document generator creates documentation
    for an entire package using pydoc's machinery.

    baseModules -- modules which will be included
        and whose included and children modules will be
        considered fair game for documentation
    destinationDirectory -- the directory into which
        the HTML documentation will be written
    recursion -- whether to add modules which are
        referenced by and/or children of base modules
    exclusions -- a list of modules whose contents will
        not be shown in any other module, commonly
        such modules as OpenGL.GL, wxPython.wx etc.
    recursionStops -- a list of modules which will
        explicitly stop recursion (i.e. they will never
        be included), even if they are children of base
        modules.
    formatter -- allows for passing in a custom formatter
        see DefaultFormatter for sample implementation.
    """
    def __init__(
        self, base_modules, destination_directory=".",
        recursion=1, exclusions=(),
        recursion_stops=(),
        formatter = None
    ):
        self.destinationDirectory = os.path.abspath(destination_directory)
        self.exclusions = {}
        self.warnings = []
        self.baseSpecifiers = {}
        self.completed = {}
        self.recursionStops = {}
        self.recursion = recursion
        for stop in recursion_stops:
            self.recursionStops[stop] = 1
        self.pending = []
        for exclusion in exclusions:
            try:
                self.exclusions[exclusion] = pydoc.locate(exclusion)
            except pydoc.ErrorDuringImport:
                self.warn('Unable to import the module {0} which was specified as an exclusion module'.format(
                    repr(exclusion))
                )
        self.formatter = formatter or DefaultFormatter()
        for base in base_modules:
            self.add_base(base)

    def warn(self, message):
        """Warnings are used for recoverable, but not necessarily ignorable conditions"""
        self.warnings.append(message)

    def info(self, message):
        """Information/status report"""
        _log.debug(message)

    def add_base(self, specifier):
        """Set the base of the documentation set, only children of these modules will be documented"""
        try:
            self.baseSpecifiers[specifier] = pydoc.locate(specifier)
            self.pending.append(specifier)
        except pydoc.ErrorDuringImport:
            self.warn('Unable to import the module {0} which was specified as a base module'.format(
                repr(specifier)
            ))

    def add_interesting(self, specifier):
        """Add a module to the list of interesting modules"""
        if self.check_scope(specifier):
            self.pending.append(specifier)
        else:
            self.completed[specifier] = 1

    def check_scope(self, specifier):
        """Check that the specifier is "in scope" for the recursion"""
        if not self.recursion:
            return 0
        items = specifier.split('.')
        stop_check = items[:]
        while stop_check:
            name = '.'.join(items)
            if self.recursionStops.get(name):
                return 0
            elif self.completed.get(name):
                return 0
            del stop_check[-1]
        while items:
            if self.baseSpecifiers.get('.'.join(items)):
                return 1
            del items[-1]
        # was not within any given scope
        return 0

    def process(self):
        """Having added all of the base and/or interesting modules,
        proceed to generate the appropriate documentation for each
        module in the appropriate directory, doing the recursion
        as we go."""
        try:
            while self.pending:
                try:
                    if self.pending[0] in self.completed:
                        raise AlreadyDone(self.pending[0])
                    self.info('Start {0}'.format(repr(self.pending[0])))
                    obj = pydoc.locate(self.pending[0])
                    self.info('   ... found {0}'.format(repr(obj.__name__)))
                except AlreadyDone:
                    pass
                except pydoc.ErrorDuringImport as value:
                    self.info('   ... FAILED ' + repr(value))
                    self.warn('Unable to import the module ' + repr(self.pending[0]))
                except (SystemError, SystemExit) as value:
                    self.info('   ... FAILED ' + repr(value))
                    self.warn('Unable to import the module ' + repr(self.pending[0]))
                except Exception as value:
                    self.info('   ... FAILED ' + repr(value))
                    self.warn('Unable to import the module ' + repr(self.pending[0]))
                else:
                    page = self.formatter.page(
                        pydoc.describe(obj),
                        self.formatter.docmodule(
                            obj,
                            obj.__name__,
                            package_context=self,
                        )
                    )
                    file_name = os.path.join(
                        self.destinationDirectory,
                        self.pending[0] + ".html",
                    )
                    file = open(file_name, 'w')
                    file.write(page)
                    file.close()
                    self.completed[self.pending[0]] = obj
                del self.pending[0]
        finally:
            for item in self.warnings:
                _log.info(item)

    def clean(self, object_list, obj):
        """callback from the formatter object asking us to remove
        those items in the key, value pairs where the object is
        imported from one of the excluded modules"""
        for key, value in object_list[:]:
            for excludeObject in self.exclusions.values():
                if hasattr(excludeObject, key) and excludeObject is not obj:
                    if getattr(excludeObject, key) is value or\
                            (hasattr(excludeObject, '__name__') and excludeObject.__name__ == "Numeric"):
                        object_list[:] = [(k, o) for k, o in object_list if k != key]

    def recurse_scan(self, object_list):
        """Process the list of modules trying to add each to the
        list of interesting modules"""
        for key, value in object_list:
            self.add_interesting(value.__name__)

#---------------------------------------------------------------------------#         
# Main Runner
#---------------------------------------------------------------------------#         
if __name__ == "__main__":
    if not os.path.exists("./html"):
        os.mkdir("./html")

    print("Building Pydoc API Documentation")
    doc_gen = PackageDocumentationGenerator(
        base_modules=['pymodbus3', '__builtin__'],
        destination_directory="./html/",
        exclusions=['math', 'string', 'twisted'],
        recursion_stops=[],
    )
    doc_gen.process()

    if os.path.exists('../../../build'):
        shutil.move("html", "../../../build/pydoc")
