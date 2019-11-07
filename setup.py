# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

DISTNAME = 'ppno'
VERSION = '0.1.2'
PACKAGES = find_packages()
LONG_DESCRIPTION = open('README.md', encoding="utf8").read()

setup(name='ppno',
      version=VERSION,
      packages=PACKAGES,
      description='Pressurized Pipe Network Optimizer',
      long_description=LONG_DESCRIPTION,
      long_description_content_type='text/markdown',
      author='Andrés García Martínez',
      author_email='ppnoptimizer@gmail.com',
      license='Apache 2.0',
      url='https://github.com/andresgciamtez/ppno'
     )
