import os
import sys

from sphinx.ext import autodoc


sys.path.insert(0, os.path.abspath('..'))

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_css_files = ['css/custom.css']

project = 'ImSwitch'
copyright = '2020, 2021 TestaLab'


class ClassCondensedHeaderDocumenter(autodoc.ClassDocumenter):
    """ Class documenter that only prints out the class name in the header. """

    objtype = 'classconheader'

    def add_directive_header(self, sig):
        self.add_line(f'.. class:: {self.format_name()}', self.get_sourcename())


def setup(app):
    app.add_autodocumenter(ClassCondensedHeaderDocumenter)
