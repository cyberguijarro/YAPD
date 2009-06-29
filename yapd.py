#!/usr/bin/python

"""
tom - Copyright 2009 Emilio Guijarro Cameros (cyberguijarro@gmail.com)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import subprocess
import sys
import os
import time

def execute(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    exitCode = process.wait()

    if exitCode:
        output = process.stderr.readlines()
    else:
        output = process.stdout.readlines()

    return (exitCode, output)

def value(key, lines):
    result = None

    for line in lines:
        try:
            if line.split(' ')[1] == key:
                trailer = line.split(' ')[2:]

                if len(trailer) > 1:
                    result = ' '.join(trailer).rstrip()
                else:
                    result = trailer[0].rstrip()
        except:
            pass

    return result

def die(exitCode, error):
   
    if exitCode != 0:
        print 'Error:'

        if error is str:
            print error
        else:
            print "".join(error)

        exit()

(exitCode, output) = execute(['p4', 'opened'])
die(exitCode, output)
changes = sys.argv[1:]

for line in output:
    file = line.split("#")[0]

    # Find out what change the file belongs to
    if line.split("#")[1].split(' ')[3] == 'change':
        change = line.split("#")[1].split(' ')[4]
    else:
        change = 'default'

    if (len(changes) == 0) or (change in changes):

        (exitCode, stat) = execute(['p4', 'fstat', file])
        die(exitCode, output)
        depotFile = value('depotFile', stat)

        # Depot date is not available when file is new
        try:
            depotDate = float(value('headTime', stat))
        except TypeError:
            depotDate = 0.0

        clientFile = value('clientFile', stat)

        # Client date is not available when file has been deleted
        try:
            clientDate = os.stat(clientFile).st_mtime
        except OSError:
            clientDate = 0.0

        action = value('action', stat)

        print 'diff -Naur %s %s' % (depotFile, clientFile)
        print '--- %s\t%s' % (depotFile, time.strftime("%Y-%m-%d %H:%M:%S.000000000 +0000", time.gmtime(depotDate)))
        print '+++ %s\t%s' % (clientFile, time.strftime("%Y-%m-%d %H:%M:%S.000000000 +0000", time.gmtime(clientDate)))

        if action == 'edit':
            (exitCode, diff) = execute(['p4', 'diff', '-du', file])
            die(exitCode, output)
                
            for change in diff[1:]:
                print change,

        elif action == 'add':
            fileStream = open(clientFile, 'r')           
            contents = fileStream.readlines()
            print '@@ -0,0 +1,%s @@' % len(contents)

            for content in contents:
                print '+%s' % content,

            fileStream.close()
        elif action == 'delete':
            # Temporarily recover file
            (exitCode, dummy) = execute(['p4', 'revert', file])
            die(exitCode, dummy)
            fileStream = open(clientFile, 'r')
            contents = fileStream.readlines()
            print '@@ -1,%s +0,0 @@' % len(contents)

            for content in contents:
                print '-%s' % content,

            fileStream.close()
            # Delete file again
            execute(['p4', 'delete', '-c', change, file])
            die(exitCode, dummy)

        print ''
