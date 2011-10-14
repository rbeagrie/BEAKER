from distutils.core import setup
import py2exe,os,matplotlib

opts = {
    'py2exe': {'dll_excludes': ['MSVCP90.dll'],
               'dist_dir' : 'Binaries\\Win32',
               'compressed' : True
              }
       }

files = matplotlib.get_py2exe_datafiles()
files.append(('.',['Beaker.ico']))
files.append(('.',['Beaker.gif']))
files.append(('.',['help.chm']))
files.append(('Tutorial',['Tutorial/tutorial concentration data.txt']))
files.append(('Tutorial',['Tutorial/tutorial rate data.txt']))

setup(windows=[{'script':'__init__.py',
                'dest_base':'Beaker',
                'icon_resources':[(0,'Beaker.ico')]}],
      data_files=files,
      options=opts)
