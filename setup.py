# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from distutils.core import Extension

DISTNAME = 'ppno'
VERSION = '0.1.0'
PACKAGES = find_packages()
EXTENSIONS = []
DESCRIPTION = 'Pressurized Pipe Network Optimizer'
LONG_DESCRIPTION = open('README.md', encoding="utf8").read()
AUTHOR = 'Andrés García Martínez'
MAINTAINER_EMAIL = 'ppnoptimizer@gmail.com'
LICENSE = 'Apache 2.0'
URL = 'https://github.com/andresgciamtez/ppno'

setuptools_kwargs = {
    'zip_safe': False,
    'install_requires': [],
    'scripts': [],
    'include_package_data': True
}

setup(name=DISTNAME,
      version=VERSION,
      packages=PACKAGES,
      ext_modules=EXTENSIONS,
      description=DESCRIPTION,
      long_description=LONG_DESCRIPTION,
      author=AUTHOR,
      maintainer_email=MAINTAINER_EMAIL,
      license=LICENSE,
      url=URL,
**setuptools_kwargs)
