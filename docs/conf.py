import os
import sys

from sphinx.ext import autodoc


sys.path.insert(0, os.path.abspath('..'))

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']

html_theme = 'sphinx_rtd_theme'


class ClassDocstrDocumenter(autodoc.ClassDocumenter):
    """ Class documenter that only prints the docstring. """

    objtype = 'classdocstr'

    def add_directive_header(self, sig):
        self.add_line(f'.. class:: {self.format_name()}', self.get_sourcename())


def setup(app):
    app.add_autodocumenter(ClassDocstrDocumenter)
