# 
# Copyright (C) 2006 Zach Tibbitts <zach@collegegeek.org>
# Copyright (C) 2006 Alon Zakai ('Kripken') <kripkensteiner@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#

# pytorrent-manager: backend/non-gui routines, that are not part of the core
# pytorrent module. pytorrent itself is mainly an interface to libtorrent,
# with some arrangements of exception classes for Python, etc.; also, some
# additional code that fits in well at the C++ level of libtorrent. All other
# backend routines should be in pytorrent-manager.
#
# Things which pytorrent-manager should do:
#
# 1. Save/Load torrent states (list of torrents in system, + their states) to file
#    (AutoSaveTorrents in deluge.py)
# 2. Manage basic queuing: how many active downloads, and autopause the rest (this
#    is currently spread along deluge.py and torrenthandler.py)
# 2a.Queue up and queue down, etc., functions (in deluge.py)
# 3. Save/Load a preferences file, with all settings (max ports, listen port, use
#    DHT, etc. etc.)
# 4. Manage autoseeding to a certain share % (currently in torrenthandler.py)
# 5. Handle caching of .torrent files and so forth (currently in deluge.py)
# 6. A 'clear completed' function, that works on the BACKEND data, unlike the
#    current implementation which works on the frontend (in torrenthander.py)
# 7. Various statistics-reporting functions - # of active torrents, etc. etc.
#    (getNumActiveTorrents in torrenthandler.py)
# 8. Remove torrent's data (in deluge.py)
#

import pytorrent_core
import os
import pickle

class torrent:
	def __init__(self, filename, save_dir, compact):
		self.filename = filename
		self.save_dir = save_dir
		self.compact  = compact



static PyObject *torrent_get_file_info(PyObject *self, PyObject *args)
{
	python_long unique_ID;
	if (!PyArg_ParseTuple(args, "i", &unique_ID))
		return NULL;

	long index = get_index_from_unique_ID(unique_ID);
	if (PyErr_Occurred())
		return NULL;

	std::vector<PyObject *> temp_files;

	PyObject *file_info;

	std::vector<float> progresses;

	torrent_t &t = M_torrents->at(index);
	t.handle.file_progress(progresses);

	torrent_info::file_iterator start =
		t.handle.get_torrent_info().begin_files();
	torrent_info::file_iterator end   =
		t.handle.get_torrent_info().end_files();

	long fileIndex = 0;

	filter_out_t &filter_out = t.filter_out;

	for(torrent_info::file_iterator i = start; i != end; ++i)
	{
		file_entry const &currFile = (*i);

		file_info = Py_BuildValue(
								"{s:s,s:d,s:d,s:f,s:i}",
								"path",				currFile.path.string().c_str(),
								"offset", 			double(currFile.offset),
								"size", 				double(currFile.size),
								"progress",			progresses[i - start]*100.0,
								"filtered_out",	long(filter_out.at(fileIndex))
										);

		fileIndex++;

		temp_files.push_back(file_info);
	};

	PyObject *ret = PyTuple_New(temp_files.size());
	
	for (unsigned long i = 0; i < temp_files.size(); i++)
		PyTuple_SetItem(ret, i, temp_files[i]);

	return ret;
};

static PyObject *torrent_set_filter_out(PyObject *self, PyObject *args)
{
	python_long unique_ID;
	PyObject *filter_out_object;
	if (!PyArg_ParseTuple(args, "iO", &unique_ID, &filter_out_object))
		return NULL;

	long index = get_index_from_unique_ID(unique_ID);
	if (PyErr_Occurred())
		return NULL;

	torrent_t &t = M_torrents->at(index);
	long num_files = t.handle.get_torrent_info().num_files();
	assert(PyList_Size(filter_out_object) ==  num_files);

	for (long i = 0; i < num_files; i++)
	{
		t.filter_out.at(i) =
			PyInt_AsLong(PyList_GetItem(filter_out_object, i));
	};

	t.handle.filter_files(t.filter_out);

	Py_INCREF(Py_None); return Py_None;
}


	// Shut down torrents gracefully
	for (long i = 0; i < Num; i++)
		internal_remove_torrent(0);


struct torrent_t {
	torrent_handle handle;
	unique_ID_t    unique_ID;
	filter_out_t   filter_out;
	torrent_name_t name;
};

typedef std::vector<torrent_t> torrents_t;
typedef torrents_t::iterator   torrents_t_iterator;

class state:
	def __init__:
		self.max_connections = 60 # Etc. etc. etc.

		# Prepare queue (queue is pickled, just like everything else)
		self.queue = [] # queue[x] is the unique_ID of the x-th queue position. Simple.

		# Torrents
		self.torrents = []
		self.unique_IDs = {}

class manager:
	def __init__(self, state_filename):
		print "Init"

		self.state_filename = state_filename

		# Unpickle the state
		try:
			pkl_file = open(state_filename, 'rb')
			self.state = pickle.load(pkl_file)
			pkl_file.close()
		except IOError:
			self.state = new state()

		# How does the queue get updated? Use biology


	def add_torrent(self, filename, save_dir, compact)
		unique_ID = pytorrent_core.add_torrent(filename, save_dir, compact)

	def quit(self):
		# Pickle the state
		output = open(self.state_filename, 'wb')
		pickle.dump(self.state, output)
		output.close()
