# -*- coding: utf-8 -*-

from setuptools import setup

setup(name='ppno',
      version='0.1.8',
      description='Pressurized Pipe Network Optimizer',
      long_description=open('README.md', encoding="utf8").read(),
      long_description_content_type='text/markdown',
      author='Andrés García Martínez',
      author_email='ppnoptimizer@gmail.com',
      packages=['ppno'],
      include_package_data=True,       
      url='https://github.com/andresgciamtez/ppno',
      install_requires=['numpy', 'scipy', 'pygmo'],
      classifiers=["Programming Language :: Python :: 3",
                   "License :: OSI Approved :: Apache Software License",
                   "Operating System :: OS Independent"
		   ]
      )
