# coding=utf-8
from StringIO import StringIO
import os
import gzip
import urllib2
import json


def uncompressed_io(file_like):
    """read a compressed file like stream, uses gzip, return file-oject"""

    buf = StringIO(file_like.read())
    f = gzip.GzipFile(fileobj=buf)
    return f


def open_url(url):
    """Send a request to url, return the respones"""

    try:
        request = urllib2.Request(url)
        request.add_header('Accept-Encoding', 'gzip')
        response = urllib2.urlopen(request)
        return response
    except urllib2.HTTPError as e:
        print 'HTTP error reading url:', url
        print 'Code', e.code
        print 'Returns', e.read()
    except urllib2.URLError as e:
        print 'URL error reading url:', url
        print 'Reason:', e.reason

    return None


def get_file_response(url, dest):
    """read response from url, save it to dest, returns a filename.
    dest should be a directory
    filename is derived from url or 'unknown.dat'
    """

    data = get_data_response(url)
    if not data:
        return None

    # get file name from url
    file_name = url.split('/')[-1].split('?')[0]
    if not file_name:
        file_name = 'unknown.dat'  # a default

    # join with destination dir
    file_name = os.path.realpath(os.path.join(dest, file_name))
    # open, write and close
    savefile = open(file_name, 'wb')
    savefile.write(data)
    savefile.close()
    # return saved file name
    return file_name


def get_json_response(url):
    """load a json structure from a Rest-URL, returns a list/dict python object"""

    # read from http with url
    response = open_url(url)
    if response.info().get('Content-Encoding') == 'gzip':
        data = json.load(uncompressed_io(response))
    else:
        data = json.load(response)

    return data


def mask_url_string(url_str):
    return url_str.replace(u" ", u'%20').replace(u'Ö', u'%C3%96').replace(u'Ä', u'%C3%84').replace(u'Ü', u'%C3%9C')


def uncompress_buffer(buffer):
    buf = StringIO(buffer)
    f = gzip.GzipFile(fileobj=buf)
    data = f.read()
    return data


def get_data_response(url):
    """download into data buffer"""

    data = ""
    response = open_url(url)
    if not response:
        return data

    block_sz = 8192
    while True:
        buffer = response.read(block_sz)
        if not buffer:
            break
        if not data:
            data = buffer
        else:
            data += buffer

    response.close()
    if response.info().get('Content-Encoding') == 'gzip':
        data = uncompress_buffer(data)

    return data
