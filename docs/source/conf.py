# -*- coding: utf-8 -*-
#
# Deluge documentation build configuration file
#
# This file is execfile()d with the current directory set to its containing dir.
#
# The contents of this file are pickled, so don't put values in the namespace
# that aren't pickleable (module imports are okay, they're removed automatically).
#
# All configuration values have a default value; values that are commented out
# serve to show the default value.

import os
import sys
from datetime import date

from recommonmark.states import DummyStateMachine
from recommonmark.transform import AutoStructify
from six.moves import builtins
from sphinx.ext import apidoc
from sphinx.ext.autodoc import ClassDocumenter, bool_option

# If your extensions are in another directory, add it here. If the directory is relative
# to the documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.join(os.path.dirname(__file__), os.path.pardir), os.path.pardir
        )
    )
)
# Importing version only possible after add project root to sys.path.
try:
    from version import get_version
except ImportError:
    from deluge.common import get_version


# General configuration
# ---------------------

needs_sphinx = '2.0'
suppress_warnings = ['app.add_source_parser']

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.napoleon',
    'sphinx.ext.coverage',
    'sphinxcontrib.spelling',
]

napoleon_include_init_with_doc = True
napoleon_use_rtype = False

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_parsers = {'.md': 'recommonmark.parser.CommonMarkParser'}
source_suffix = ['.rst', '.md']

# The master toctree document.
master_doc = 'index'

# General substitutions.
project = 'Deluge'
current_year = date.today().year
copyright = '2008-%s, Deluge Team' % current_year  # noqa: A001

# The full version, including alpha/beta/rc tags.
release = get_version()
# The short X.Y version.
version = '.'.join(release.split('.', 2)[:2])

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
# today = ''
# Else, today_fmt is used as the format for a strftime call.
today_fmt = '%B %d, %Y'

# List of documents that shouldn't be included in the build.
# unused_docs = []

# List of directories, relative to source directories, that shouldn't be searched
# for source files.
exclude_patterns = []

# The reST default role (used for this markup: `text`) to use for all documents.
# default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
# add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
# add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
# show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# Options for spelling
# --------------------
spelling_show_suggestions = True
spelling_word_list_filename = '../spelling_wordlist.txt'
# Skip Deluge module rst files
if 'spelling' in sys.argv or 'spellcheck_docs' in sys.argv:
    exclude_patterns += ['modules']

# Options for HTML output
# -----------------------
html_theme = 'sphinx_rtd_theme'
# The style sheet to use for HTML and HTML Help pages. A file of that name
# must exist either in Sphinx' static/ path, or in one of the custom paths
# given in html_static_path.
# html_style = 'default.css'

# Add font-mfizz for icons.
html_css_files = [
    'https://cdnjs.cloudflare.com/ajax/libs/font-mfizz/2.4.1/font-mfizz.min.css'
]
# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
# html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
# html_short_title = None

# The name of an image file (within the static path) to place at the top of
# the sidebar.
# html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = '../../deluge/ui/data/pixmaps/deluge.ico'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
# html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
# html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
# html_additional_pages = {}

# If false, no module index is generated.
# html_use_modindex = True

# If false, no index is generated.
# html_use_index = True

# If true, the index is split into individual pages for each letter.
# html_split_index = False

# If true, the reST sources are included in the HTML build as _sources/<name>.
# html_copy_source = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
# html_use_opensearch = ''

# If nonempty, this is the file name suffix for HTML files (e.g. ".xhtml").
# html_file_suffix = ''

# Output file base name for HTML help builder.
htmlhelp_basename = 'delugedoc'


# Options for LaTeX output
# ------------------------

# The paper size ('letter' or 'a4').
# latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
# latex_font_size = '10pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, document class [howto/manual]).
latex_documents = [
    ('index', 'deluge.tex', 'deluge Documentation', 'Deluge Team', 'manual')
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
# latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
# latex_use_parts = False

# Additional stuff for the LaTeX preamble.
# latex_preamble = ''

# Documents to append as an appendix to all manuals.
# latex_appendices = []

# If false, no module index is generated.
# latex_use_modindex = True


# Autodoc section
# ---------------
class Mock(object):

    __all__ = []

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return ''

    @classmethod
    def __getattr__(cls, name):
        if name in ('__file__', '__path__', 'xdg_config_home'):
            return '/dev/null'
        elif name[0] == name[0].upper():
            mock_type = type(name, (), {})
            mock_type.__module__ = __name__
            return mock_type
        else:
            return Mock()

    def __add__(self, other):
        return other

    def __or__(self, __):
        return Mock()


# Use custom mock as autodoc_mock_imports fails to handle these modules.
MOCK_MODULES = ['deluge._libtorrent', 'xdg', 'xdg.BaseDirectory']

for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = Mock()

# Must add these for autodoc to import packages successfully
builtins.__dict__['_'] = lambda x: x
builtins.__dict__['_n'] = lambda s, p, n: s if n == 1 else p

autodoc_mock_imports = [
    'twisted',
    'rencode',
    'OpenSSL',
    'PIL',
    'libtorrent',
    'psyco',
    'gi',
    'cairo',
    'curses',
    'win32api',
    'win32file',
    'win32process',
    'win32pipe',
    'pywintypes',
    'win32con',
    'win32event',
    'pytest',
    'mock',
    'mako',
    'xdg',
    'zope',
    'zope.interface',
]

# Register an autodoc class directive to only include exported methods.
ClassDocumenter.option_spec['exported'] = bool_option


def maybe_skip_member(app, what, name, obj, skip, options):
    if options.exported and not (
        hasattr(obj, '_rpcserver_export') or hasattr(obj, '_json_export')
    ):
        return True


# Monkey patch to fix recommonmark 0.4 doc reference issues.
orig_run_role = DummyStateMachine.run_role


def run_role(self, name, options=None, content=None):
    if name == 'doc':
        name = 'any'
    return orig_run_role(self, name, options, content)


DummyStateMachine.run_role = run_role


# Run the sphinx-apidoc to create package/modules rst files for autodoc.
def run_apidoc(__):
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    module_dir = os.path.join(cur_dir, '..', '..', 'deluge')
    ignore_paths = [
        os.path.join(module_dir, 'plugins'),
        os.path.join(module_dir, 'tests'),
    ]
    argv = [
        '--force',
        '--no-toc',
        '--output-dir',
        os.path.join(cur_dir, 'modules'),
        module_dir,
    ] + ignore_paths
    apidoc.main(argv)


def setup(app):
    app.connect('builder-inited', run_apidoc)
    app.connect('autodoc-skip-member', maybe_skip_member)
    app.add_config_value('recommonmark_config', {}, True)
    app.add_transform(AutoStructify)
