#!/usr/bin/env python

# webcheck.py - main module of webcheck doing command-line checking
#
# Copyright (C) 1998, 1999 Albert Hopkins (marduk) <marduk@python.net>
# Copyright (C) 2002 Mike Meyer <mwm@mired.org>
# Copyright (C) 2005 Arthur de Jong <arthur@tiefighter.et.tudelft.nl>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.


explored = []
problem_db = {}
linkMap = {}

import sys
import time
import os


start_time = time.ctime(time.time())

# importing the config.py file is a real problem if the user did not install
# the files EXACTLY the way I said to... or even using the frozen version is
# becoming a real bitch.  I will just have to tell them right out how to fix it.
try:
    sys.path = ['.'] + sys.path
    import config
except ImportError:
    sys.stdout.write('Please verify that PYTHONPATH knows where to find "config.py"\n')
    sys.exit(1)

import myUrlLib
Link=myUrlLib.Link

# myUrlLib will be looking for a 'config' module.  set it up here.
myUrlLib.config=config

import debugio
debugio.DEBUG_LEVEL = config.DEBUG_LEVEL

import version

def print_version():
    """print version information"""
    print \
        "webcheck "+version.webcheck+"\n" \
        "Written by Albert Hopkins (marduk), Mike Meyer and Arthur de Jong.\n" \
        "\n" \
        "Copyright (C) 1998, 1999, 2002, 2005 Albert Hopkins (marduk), Mike Meyer\n" \
        "and Arthur de Jong.\n" \
        "This is free software; see the source for copying conditions.  There is NO\n" \
        "warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE."

def print_usage():
    """print short usage information"""
    print >>sys.stderr, \
        "Usage: webcheck [OPTION]... URL"

def print_tryhelp():
    """print friendly pointer to more information"""
    print >>sys.stderr, \
        "Try `webcheck --help' for more information."

def print_help():
    """print option list"""
    print \
        "Usage: webcheck [OPTION]... URL\n" \
        "Generate report for the given URL\n" \
        "\n" \
        "  -x PATTERN     mark URLs matching PATTERN as external\n" \
        "  -y PATTERN     do not check URLs matching PATTERN\n" \
        "  -l URL         use URL as logo for the report\n" \
        "  -b             base URLs only: consider any URL not starting with the base\n" \
        "                 URL to be external\n" \
        "  -a             do not check external URLs\n" \
        "  -q, --quiet, --silent\n" \
        "                 do not print out progress as webcheck traverses a site\n" \
        "  -o DIRECTORY   the directory in which webcheck will generate the reports\n" \
        "  -f, --force    overwrite files without asking\n" \
        "  -r N           the amount of redirects Webcheck should follow when following\n" \
        "                 a link, 0 implies follow all redirects.\n" \
        "  -w, --wait=SECONDS\n" \
        "                 wait SECONDS between retrievals\n" \
        "  -V, --version  output version information and exit\n" \
        "  -h, --help     display this help and exit\n" \
        "  -d LEVEL       set loglevel to LEVEL, for programmer-level debugging"

def parse_args():
    """parse command-line arguments"""
    import getopt
    try:
        optlist, args = getopt.gnu_getopt(sys.argv[1:],
            "x:y:l:baqo:fr:w:Vhd:",
            ["quiet","silent","force","wait=","version","help"])
    except getopt.error, reason:
        print >>sys.stderr,"webcheck: %s" % reason;
        print_tryhelp()
        sys.exit(1)
    for flag,arg in optlist:
        if flag=='-x':
            config.EXCLUDED_URLS.append(arg)
        elif flag=='-y':
            config.YANKED_URLS.append(arg)
        elif flag=='-l':
            config.LOGO_HREF=arg
        elif flag=='-b':
            config.BASE_URLS_ONLY=1
        elif flag=='-a':
            config.AVOID_EXTERNAL_LINKS=1
        elif flag in ("-q","--quiet","--silent"):
            debugio.DEBUG_LEVEL=0
        elif flag=='-o':
            config.OUTPUT_DIR=arg
        elif flag in ("-f","--force"):
            config.OVERWRITE_FILES=1
        elif flag=='-r':
            config.REDIRECT_DEPTH=int(arg)
        elif flag in ("-w","--wait"):
            config.WAIT_BETWEEN_REQUESTS=int(arg)
        elif flag in ("-V","--version"):
            print_version()
            sys.exit(0)
        elif flag in ("-h","--help"):
            print_help()
            sys.exit(0)
        elif flag=='-d':
            debugio.DEBUG_LEVEL=int(arg)
    if len(args)==0:
        print_usage()
        print_tryhelp()
        sys.exit(1)
    else:
        global URL
        URL = args[0]
    config.HOSTS = config.HOSTS + args[1:]

def warn():
    """Warn the user that something has gone wrong."""
    print "*******************************************"
    print "*                                         *"
    print "* Warning, Webcheck has found nothing to  *"
    print "* report for this site.  If you feel this *"
    print "* is in error, please contact             *"
    print "* %s.                                     *" % version.author
    print "* and specify the environment that caused *"
    print "* this to occur.                          *"
    print "*                                         *"
    print "* Webcheck %s                             *" % version.webcheck
    print "*                                         *"
    print "*******************************************"

def link_image(filename):
    source = '/usr/share/webcheck/' + filename
    target = config.OUTPUT_DIR + filename
    if os.path.exists(target): return
    try:
       os.symlink(source, target)
    except os.error, (errcode, errtext):
       print 'Warning: "%s": %s' % (target, errtext)
       print '         Please copy "%s" to "%s".' % (source, target)

# set up the pages
plugins = config.PLUGINS

if __name__ == '__main__':

    parse_args()
    config.OUTPUT_DIR=config.OUTPUT_DIR + '/'

    debugio.write('checking site....')
    try:
        Link.base = Link(URL,None) # this will take a while
    except KeyboardInterrupt:
        sys.stderr.write("Interrupted\n")
        sys.exit(1)
    debugio.write('done.')
    if not hasattr(Link.base,"URL"):
        warn()
        sys.exit(1)

    linkMap = Link.linkMap

    # now we can write out the files
    # start with the frame-description page
    debugio.write('Generating reports...')
    from plugins.rptlib import main_index, nav_bar
    main_index()
    nav_bar(plugins)
    link_image('blackbar.png')
    if config.LOGO_HREF == 'webcheck.png': link_image('webcheck.png')
    debugio.write('done.')

