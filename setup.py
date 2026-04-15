from setuptools import setup, find_packages

setup(
    name='ppno',
    version='0.3.2',
    description='Pressurized Pipe Network Optimizer',
    long_description=open('README.md', encoding="utf8").read(),
    long_description_content_type='text/markdown',
    author='Andrés García Martínez',
    author_email='ppnoptimizer@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    url='https://github.com/andresgciamtez/ppno',
    project_urls={
        "Bug Tracker": "https://github.com/andresgciamtez/ppno/issues",
    },
    keywords="water-networks optimization epanet hydraulics pipe-sizing",
    python_requires='>=3.8',
    install_requires=[
        'numpy>=1.20.0',
        'scipy>=1.7.0',
        'pygmo>=2.18.0',
        'entoolkit'
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'build',
            'twine'
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
    ],
    entry_points={
        'console_scripts': [
            'ppno=ppno.ppno:main',
        ],
    },
)
