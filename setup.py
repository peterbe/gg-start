from os import path
from setuptools import setup


setup(
    name='gg-start',
    version='0.0.1',
    description='Plugin for gg for starting branches',
    long_description=open(path.join(_here, 'README.rst')).read(),
    py_modules=['start'],
    author='Peter Bengtsson',
    author_email='mail@peterbe.com',
    url='https://github.com/peterbe/gg-start'
    license='MIT',
    py_modules=['start'],
    install_requires=['gg'],
    entry_points="""
        [gg.plugin]
        cli=start.start
    """,
)
