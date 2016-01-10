# -*- coding: utf-8 -*-

from __future__ import (unicode_literals, division, absolute_import, print_function)

__license__ = 'GPL 3'
__copyright__ = '2016, Alex Kosloff <pisatel1976@gmail.com>'
__docformat__ = 'restructuredtext en'

import os
import re
from contextlib import closing
from time import time
import json
import mechanize
import mimetypes
import urllib
import urllib2
import StringIO
import tempfile
from base64 import b64encode

try:
	from PyQt4.Qt import QModelIndex
except:
	from PyQt5.Qt import QModelIndex

from calibre import browser, url_slash_cleaner
from calibre.web import get_download_filename
from calibre.ebooks import BOOK_EXTENSIONS
from calibre.gui2.ui import get_gui
from calibre.ptempfile import PersistentTemporaryDirectory
from calibre.utils.filenames import ascii_filename
from calibre.utils.zipfile import ZipFile
from calibre.ebooks.metadata.opf2 import OPF, metadata_to_opf

from calibre_plugins.arg_plugin.config import prefs

class ArgAPI(object):
	def __init__(self, gui):
		print('new a*rg api interface created')
		self.tdir = PersistentTemporaryDirectory('_add_books')
		self.base_url = prefs['base_url']

	def _get(self, values, path='/api/do'):
		''' Gets something from the api listener url '''
		self.base_url = prefs['base_url']
		url = url_slash_cleaner(self.base_url + path)
		user_agent = 'Casanova/1.0 (compatible; MSIE 5.5; Windows NT)'
		req = urllib2.Request(url)
		response = urllib2.urlopen(req)
		return response

	def _get_json(self, values, path):
		''' Utility to get json response '''
		response = self._get(values, path)
		the_content = response.read()
		try: 
			doc = json.loads(the_content)
		except:
			doc = {}
		return doc

	def _post(self, values, path='/api/do'):
		''' Posts something to the api listener url '''
		prefs.refresh()
		self.base_url = prefs['base_url']
		url = url_slash_cleaner(self.base_url + path)
		user_agent = 'Casanova/1.0 (compatible; MSIE 5.5; Windows NT)'
		values['un'] = prefs['username']
		values['pw'] = prefs['password']
		headers = { 'User-Agent' : user_agent, 'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8' }
		data = urllib.urlencode(values)
		req = urllib2.Request(url, data, headers)
		response = urllib2.urlopen(req)
		return response

	def _post_metadata(self, id, version, opf, cover=None):
		''' Posts updated metadata to server '''
		uri = '/thing/%s/calibre/commit' % id
		print("Committing changes to: " + uri)
		values = {'version' : version,
		          'opf' : opf }
		if cover:
			with open(cover, 'rb') as f:
				cd = f.read()
				values['cover'] = b64encode(cd)
				fn, ext = os.path.splitext(cover)
				values['cover_ext'] = ext
		response = self._post(values, uri)
		the_page = response.read()
		try: 
			doc = json.loads(the_page)
		except:
			doc = {}
		if 'message' in doc:
			return doc['message']
		else:
			return "Something went wrong"

	def get_arg_ids(self):
		data = get_gui().current_db.get_data_as_dict(None, authors_as_string=True, convert_to_local_tz=False)	
		ids = {}
		for d in data:
			identifiers = d['identifiers'].split(',')
			for identifier in identifiers:
				if identifier.startswith('arg:'):
					try:
						combined_id = identifier.rsplit(':',1)[1]
						arg_id, version = combined_id.split('.')
						ids[d['id']] = (arg_id, d['timestamp'],int(version))
					except:
						print('Skipping potential arg id: ', identifier)
		return ids
		#get_gui().current_db.library_view.model()


	def commit(self, book_id):
		''' Commits any local changes to the metadata for this book up to the server '''
		ids = self.get_arg_ids()
		if book_id not in ids:
			print('There is no a*rg identifier for this book')
			return
		arg_id, timestamp, version = ids[book_id]
		repo_version = self.arg_book_status(arg_id)
		if version!=repo_version:
			print('This library\'s version is out of date.')
			return
		# recompute the id
		mi = get_gui().current_db.get_metadata(book_id, index_is_id=True, get_cover=True)
		mi.identifiers['arg'] = "%s.%s" % (mi.identifiers['arg'].split('.')[0], version+1)
		get_gui().current_db.set_metadata(book_id, mi)
		mi = get_gui().current_db.get_metadata(book_id, index_is_id=True, get_cover=True)
		# get the opf that will be posted
		opf = metadata_to_opf(mi)
		# now post the metadata
		return self._post_metadata(arg_id, version, opf, mi.cover)


	" Attempts to sync the entire library, assuming the library is based on a collection or author "
	def update_library(self):
		ids = self.get_arg_ids()
		status = self.arg_library_status()
		update_required = []
		for book_id in ids:
			arg_id, ts, version = ids[book_id]
			if arg_id in status and status[arg_id]>version:
				update_required.append(arg_id)
		if update_required:
			pass


	def commit_library(self):
		''' Commits all the changed metadata '''
		ids = self.get_arg_ids()


	def arg_library_status(self):
		''' Uses curren library type to sync '''
		db = get_gui().current_db.new_api
		type = db.pref('arg_library_type')
		id = db.pref('arg_id')
		if type and id:
			if type=='author':
				return self.arg_author_status(id)
			if type=='collection':
				return self.arg_collection_status(id)
		return {}


	def arg_collection_status(self, arg_id):
		''' Asks the server what is the current version '''
		uri = '/collection/%s/calibre/status' % arg_id
		data = self._get_json({}, uri)
		if 'data' in data:
			return data['data']
		else:
			return {}


	def arg_author_status(self, arg_id):
		''' Asks the server what is the current version '''
		uri = '/maker/%s/calibre/status' % arg_id
		data = self._get_json({}, uri)
		if 'data' in data:
			return data['data']
		else:
			return {}

	def arg_book_status(self, arg_id):
		''' Asks the server what is the current version '''
		uri = '/thing/%s/calibre/status' % arg_id
		data = self._get_json({}, uri)
		if 'data' in data and 'version' in data['data']:
			return int(data['data']['version'])
		else:
			return None


	def search_collections(self, query):
		''' Searches collections '''
		uri = '/api/search'
		values = {'type' : 'collections',
							'query' : query,
							'num' : 30 }
		response = self._post(values, uri)
		text = response.read()
		ret_dict = {}
		try: 
			doc = json.loads(text)
		except:
			return ret_dict
		if 'data' in doc:
			return doc['data']
		else:
			return ret_dict

	def search_authors(self, query):
		''' Searches authors '''
		uri = '/api/search'
		values = {'type' : 'makers',
							'query' : query,
							'num' : 30 }
		response = self._post(values, uri)
		text = response.read()
		ret_dict = {}
		try: 
			doc = json.loads(text)
		except:
			return ret_dict
		if 'data' in doc:
			return doc['data']
		else:
			return ret_dict

	def download_collection(self, id, limit_ids=None):
		''' Downloads all of an authors metadata to a path '''
		uri = '/collection/%s/calibre' % id
		print('Downloading metadata for collection: ' + uri )
		# first get the zipfile
		tdir = self.download_and_extract(uri)
		get_gui().current_db.recursive_import(tdir)

	def download_author(self, id, limit_ids=None):
		''' Downloads all of an authors metadata to a path '''
		uri = '/maker/%s/calibre' % id
		print('Downloading metadata for author: ' + uri )
		# first get the zipfile
		tdir = self.download_and_extract(uri)
		get_gui().current_db.recursive_import(tdir)

	def download_and_extract(self, uri):
		''' Downloads a zip file and extracts it  '''
		tdir = tempfile.mkdtemp(suffix='_archive', dir=self.tdir)
		response = self._get({}, uri)
		the_zip = response.read()
		io = StringIO.StringIO()
		io.write(the_zip)
		# now extract
		from calibre.utils.zipfile import ZipFile
		try:
			with ZipFile(io) as zf:
				zf.extractall(tdir)
		except Exception:
			print('Corrupt ZIP file, trying to use local headers')
			from calibre.utils.localunzip import extractall
			extractall(io, tdir)
		return tdir