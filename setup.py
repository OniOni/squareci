from setuptools import setup

setup(
    name='squareci',
    version='0.2',
    py_modules=['circleci_stats'],
    install_requires=[
        'Click',
        'requests'
    ],
    entry_points='''
        [console_scripts]
        squareci=circleci_stats:cli
    ''',
)
