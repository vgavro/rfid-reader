from setuptools import setup, find_packages

requires = [
    'PyYAML',
    'structlog',
    'click',
    'colorama',  # for better log rendering with structlog
]

# tests_requires = [
#     'pytest',
#     'pytest-runner',
# ]

setup(
    name='rfid-reader',
    version='0.0.1',
    description='http://github.com/vgavro/rfid-reader',
    long_description='http://github.com/vgavro/rfid-reader',
    license='proprietary and confidential',
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
    ],
    author='Victor Gavro',
    author_email='vgavro@gmail.com',
    url='http://github.com/vgavro/rfid-reader',
    keywords='',
    packages=find_packages(),
    install_requires=requires,
    # tests_require=tests_requires,
    entry_points={
        'console_scripts': [
            'rfid-reader=rfid_reader.cli:rfid_reader',
        ],
    }
)
