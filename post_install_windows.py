#!/usr/bin/env python

import os
import sys
import shutil
import beaker

DESKTOP_FOLDER = get_special_folder_path("CSIDL_DESKTOPDIRECTORY")
NAME = 'Beaker.lnk'

if sys.argv[1] == '-install':
    create_shortcut(
        os.path.join(sys.prefix, 'pythonw.exe'), # program
        'Open the Beaker Gui', # description
        NAME, # filename
        beaker.__file__, # parameters
        '', # workdir
        os.path.join(os.path.dirname(beaker.__file__), 'Beaker.ico'), # iconpath
    )
    # move shortcut from current directory to DESKTOP_FOLDER
    shutil.move(os.path.join(os.getcwd(), NAME),
                os.path.join(DESKTOP_FOLDER, NAME))
    # tell windows installer that we created another
    # file which should be deleted on uninstallation
    file_created(os.path.join(DESKTOP_FOLDER, NAME))

if sys.argv[1] == '-remove':
    pass
    # This will be run on uninstallation. Nothing to do.
