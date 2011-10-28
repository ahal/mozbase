# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Mozilla Corporation Code.
#
# The Initial Developer of the Original Code is
# Clint Talbert.
# Portions created by the Initial Developer are Copyright (C) 2007
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#  Clint Talbert <ctalbert@mozilla.com>
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

from optparse import OptionParser
import mozinfo
import subprocess
import shutil
import zipfile
import tarfile
import os

def install(src, dest=None, app="firefox"):
    src = os.path.realpath(src)
    assert(os.path.isfile(src))
    if not dest:
        dest = os.path.dirname(src)

    if zipfile.is_zipfile(src) or tarfile.is_tarfile(src):
        install_dir = _extract(src, dest)[0]
    elif mozinfo.isMac and src.lower().endswith(".dmg"):
        install_dir = _install_dmg(src, dest)
    elif mozinfo.isWin and os.access(src, os.X_OK):
        install_dir = _install_exe(src, dest)

    if install_dir:
        return get_binary(install_dir, app="firefox")

def get_binary(path, app="firefox"):
    if mozinfo.isWin:
        app += ".exe"
    for root, dirs, files in os.walk(path)L
        for filename in files:
            if filename == app and os.access(filename, os.X_OK):
                return os.path.realpath(filename)
    return 1

def _extract(path, extdir=None, delete=False):
    """
    Takes in a tar or zip file and extracts it to extdir
    If extdir is not specified, extracts to os.path.dirname(path)
    If delete is set to True, deletes the bundle at path
    Returns the list of top level files that were extracted
    """
    if zipfile.is_zipfile(path):
        bundle = zipfile.ZipFile(path)
        namelist = bundle.namelist()
    elif tarfile.is_tarfile(path):
        bundle = tarfile.open(path)
        namelist = bundle.getnames()
    else:
        return
    if extdir is None:
        extdir = os.path.dirname(path)
    elif not os.path.exists(extdir):
        os.makedirs(extdir)
    bundle.extractall(path=extdir)
    bundle.close()
    if delete:
        os.remove(path)
    return [os.path.join(extdir, name) for name in namelist
                if len(name.rstrip(os.sep).split(os.sep)) == 1]

def _install_dmg(src, dest):
    proc = subprocess.Popen(["hdiutil", "mount", src], shell=True, stdout=subprocess.PIPE)
    try:
        for data in proc.communicate()[0].split():
            if data.find("/Volumes/") != -1:
                appDir = data
                break
        for appFile in os.listdir(appDir):
            if appFile.endswith(".app"):
                 appName = appFile
                 break
        shutil.copytree(os.path.join(appDir, appName), dest)
    finally:
        subprocess.call(["hdiutil", "detach", appDir], stdout=open(os.devnull, "w"))
    return os.path.join(dest, appName)


# TODO probably hasn't been tested since 1.8.x
def _install_exe(src, dest):
    cmd = [src, "/S", "/D=" + os.path.normpath(dest)]
    proc = subprocess.Popen(cmd)
    proc.wait()

def cli(argv=sys.argv[1:]):
    parser = OptionParser()
    parser.add_option("-s", "--source",
                      dest="src",
                      help="Installation Source File (whatever was downloaded) -\
                            accepts zip, exe, tar.bz2, tar.gz, and dmg")
    parser.add_option("-d", "--destination",
                      dest="dest",
                      default=None,
                      help="Directory to install the application into")
    parser.add_option("--app", dest="app",
                      default="firefox",
                      help="Application to install - optional should be all lowercase if\
                            specified: firefox, mobile, thunderbird, etc")

    (options, args) = parser.parse_args(argv)
    if not options.src or not os.path.exists(os.path.realpath(options.src)):
        print "Error: must specify valid source"
        return 2

    # Run it
    if os.isdir(options.src):
        return get_binary(options.src, app=options.app)
    return install(options.src, dest=options.dest, app=options.app)

if __name__ == "__main__":
    sys.exit(cli())
