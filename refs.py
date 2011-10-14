import os,sys
if os.name == 'posix':
    basedir = os.getcwd()
    iconpath = '@' + os.path.join(basedir,'Beaker.xbm')
else:
    #basedir = os.path.split(sys.argv[0])[0]
    basedir = os.path.split(__file__)[0]
    iconpath = os.path.join(basedir,'Beaker.ico')
gifpath = os.path.join(basedir,'Beaker.gif')
versionpath = os.path.join(basedir,'version.txt')
helppath = os.path.join(basedir,'help.chm')
gitpath = os.path.join(basedir,'.git')
userhomedir = os.path.expanduser(os.path.join('~','Documents','Beaker'))
test = __file__
