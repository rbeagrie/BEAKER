#!/usr/bin/env python

from distutils.core import setup
import version

files = []
files.append('Beaker.ico')
files.append('Beaker.gif')
files.append('Beaker.xbm')
files.append('README')
files.append('help.chm')
files.append('Tutorial/tutorial concentration data.txt')
files.append('Tutorial/tutorial rate data.txt')

setup(name='Beaker',
      version=version.versionString,
      description='Beaker Easily Analyzes the Kinetics of Enzymatic Reactions',
      author='Rob Beagrie',
      author_email='rob@beagrie.com',
      url='http://rab205.github.com/BEAKER',
      packages=['beaker', 'beaker.Gui','beaker.Backend'],
      package_dir={'beaker':''},
      requires=['scipy','numpy','matplotlib'],
      provides='beaker',
      scripts=['__init__.py','post_install_windows.py'],
      package_data={'beaker':files})
