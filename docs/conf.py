project = 'SoftDsim'
copyright = '2025 Frankfurt University of Applied Sciences'
author = 'Frankfurt University of Applied Sciences'


release = '0.2.0'

extensions = [
    'myst_parser',
    'sphinx.ext.autodoc'
]
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
source_suffix = ['.rst', '.md']


html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_css_files = [
    'custom.css'
    ]
html_js_files = [
    'copy_button.js'
    ]
html_logo = "_static/logo.png"