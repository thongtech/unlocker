#!/usr/bin/env python
"""
The MIT License (MIT)

Copyright (c) 2015-2017 Dave Parsons

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the 'Software'), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from __future__ import print_function
import os
import sys
import shutil
import tarfile
import zipfile
import time

ARCH = 'x86_x64'
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
# The last version that supports darwin tools
FUSION_VERSION = '13.5.2'
FUSION_BUILD = '23775688'
FUSION_URL = f'https://softwareupdate.vmware.com/cds/vmw-desktop/fusion/{FUSION_VERSION}/{FUSION_BUILD}/universal/core/'

try:
    # For Python 3.0 and later
    # noinspection PyCompatibility
    from urllib.request import Request, urlopen
    # noinspection PyCompatibility
    from html.parser import HTMLParser
    # noinspection PyCompatibility
    from urllib.request import urlretrieve
except ImportError:
    # Fall back to Python 2
    # noinspection PyCompatibility
    from urllib2 import urlopen
    # noinspection PyCompatibility
    from HTMLParser import HTMLParser
    # noinspection PyCompatibility
    from urllib import urlretrieve


# Parse the Fusion directory page
class CDSParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.reset()
        self.HTMLDATA = []

    def handle_data(self, data):
        # Build a list of numeric data from any element
        if data.find("\n") == -1:
            if data[0].isdigit():
                self.HTMLDATA.append(data)
                self.HTMLDATA.sort(key=lambda s: [int(u) for u in s.split('.')])

    def clean(self):
        self.HTMLDATA = []


def convertpath(path):
    # OS path separator replacement funciton
    return path.replace(os.path.sep, '/')
	
def reporthook(count, block_size, total_size, start_time):
    if count == 0:
        start_time = time.time()
        return
    duration = time.time() - start_time
    progress_size = int(count * block_size)
    speed = int(progress_size / (1024 * duration)) if duration>0 else 0
    percent = min(int(count*block_size*100/total_size),100)
    time_remaining = ((total_size - progress_size)/1024) / speed if speed > 0 else 0
    sys.stdout.write("\r...%d%%, %d MB, %d KB/s, %d seconds remaining" %
                    (percent, progress_size / (1024 * 1024), speed, time_remaining))
    sys.stdout.flush()
      
# Spoofed urlopen
def spoofed_urlopen(url):
    req = Request(url)
    req.add_header('User-Agent', USER_AGENT)
    return urlopen(req)

# Spoofed urlretrieve
def spoofed_urlretrieve(url, file):
    req = Request(url)
    req.add_header('User-Agent', USER_AGENT)
    response = urlopen(req)
    total_size = response.getheader('Content-Length')
    if total_size is not None:
        total_size = int(total_size)
    bytes_so_far = 0
    start_time = time.time()

    with open(file, 'wb') as out_file:
        while True:
            buffer = response.read(8192)
            if not buffer:
                break
            out_file.write(buffer)
            bytes_so_far += len(buffer)
            block_size = len(buffer)
            count = bytes_so_far // block_size
            reporthook(count, block_size, total_size, start_time)

    return file

def main():
	# Check minimal Python version is 3.0
	if sys.version_info < (3, 0):
		sys.stderr.write('You need Python 3 or later\n')
		sys.exit(1)

	dest = os.path.dirname(os.path.abspath(__file__))

	# Re-create the tools folder
	shutil.rmtree(dest + '/tools', True)
	os.mkdir(dest + '/tools')

	print(f'Getting tools from Fusion version {FUSION_VERSION}...')

	# Setup file path
	urlcoretar = FUSION_URL + 'com.vmware.fusion.zip.tar'

	# Get the main core file
	try:
		spoofed_urlretrieve(urlcoretar, convertpath(dest + '/tools/com.vmware.fusion.zip.tar'))
	except:
		print('Couldn\'t find tools')
		return
	
	print('Extracting com.vmware.fusion.zip.tar...')
	tar = tarfile.open(convertpath(dest + '/tools/com.vmware.fusion.zip.tar'), 'r')
	tar.extract('com.vmware.fusion.zip', path=convertpath(dest + '/tools/'), filter='data')
	tar.close()
	
	print('Extracting files from com.vmware.fusion.zip...')
	cdszip = zipfile.ZipFile(convertpath(dest + '/tools/com.vmware.fusion.zip'), 'r')
	cdszip.extract('payload/VMware Fusion.app/Contents/Library/isoimages/' + ARCH + '/darwin.iso', path=convertpath(dest + '/tools/'))
	cdszip.extract('payload/VMware Fusion.app/Contents/Library/isoimages/' + ARCH + '/darwinPre15.iso', path=convertpath(dest + '/tools/'))
	cdszip.close()
	
	# Move the iso and sig files to tools folder
	shutil.move(convertpath(dest + '/tools/payload/VMware Fusion.app/Contents/Library/isoimages/' + ARCH + '/darwin.iso'), convertpath(dest + '/tools/darwin.iso'))
	shutil.move(convertpath(dest + '/tools/payload/VMware Fusion.app/Contents/Library/isoimages/' + ARCH + '/darwinPre15.iso'), convertpath(dest + '/tools/darwinPre15.iso'))
	
	# Cleanup working files and folders
	shutil.rmtree(convertpath(dest + '/tools/payload'), True)
	os.remove(convertpath(dest + '/tools/com.vmware.fusion.zip.tar'))
	os.remove(convertpath(dest + '/tools/com.vmware.fusion.zip'))
	
	print('Tools retrieved successfully')
	return
	
	
if __name__ == '__main__':
    main()
