/* python-miniupnp
 *
 * Copyright (C) Zach Tibbitts 2007 <zach@collegegeek.org>
 * 
 * 
 * You may redistribute it and/or modify it under the terms of the
 * GNU General Public License, as published by the Free Software
 * Foundation; either version 2 of the License, or (at your option)
 * any later version.
 * 
 * python-miniupnp is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with python-miniupnp.  If not, write to:
 * 	The Free Software Foundation, Inc.,
 * 	51 Franklin Street, Fifth Floor
 * 	Boston, MA  02110-1301, USA.
 */

#include <Python.h>
#include <miniupnpc.h>
#include <miniwget.h>
#include <upnpcommands.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// upnpDiscover()
static PyObject*
_upnpDiscover(PyObject* self, PyObject* args)
{
	int delay, i, k;
	if (!PyArg_ParseTuple(args, "i", &delay))
		return NULL;
	struct UPNPDev* discover = upnpDiscover(delay);
	struct UPNPDev* next = discover;
	// First, we have to find out how many elements are in the list
	i = 0;
	while(next)
	{
		i++;
		next = next->pNext;
	}
	// Turn the linked list into a python object
	PyObject* list = PyList_New(i);
	for(k=0;k<i;k++)
	{
		PyObject* tmp = Py_BuildValue("{ssssss}", "descURL", discover->descURL,
													"st", discover->st,
													"buffer", discover->buffer);
		PyList_SET_ITEM(list, k, tmp);
	}
	return list;
}

static PyObject*
_miniwget(PyObject* self, PyObject* args)
{
	char* url;
	int* size;
	if (!PyArg_ParseTuple(args, "si", &url, &size))
		return NULL;
	miniwget(url, size);
	return NULL;
}

static PyObject*
_parserootdesc(PyObject* self, PyObject* args)
{
	return NULL;
}

static PyObject*
_GetUPNPUrls(PyObject* self, PyObject* args)
{
	return NULL;
}

static PyObject*
_simpleUPnPcommand(PyObject* self, PyObject* args)
{
	int s;
	const char * url;
	const char * service;
	const char * action;
	struct UPNParg * arguments;
	char * buffer;
	int * bufsize;
	if (!PyArg_ParseTuple(args, "isssOsi", &s, &url, &service, &action,
			&arguments, &buffer, &bufsize))
		return NULL;
	int result;
	result = simpleUPnPcommand(s, url, service, action, arguments, buffer, bufsize);
	return Py_BuildValue("i", result);
}

static PyMethodDef upnp_methods[] = {
	{"simple_upnp_command", (PyCFunction)_simpleUPnPcommand, METH_VARARGS, "."},
	{"discover", (PyCFunction)_upnpDiscover, METH_VARARGS, "."},
	{"miniwget", (PyCFunction)_miniwget, METH_VARARGS, "."},
	{"parse_root_desc", (PyCFunction)_parserootdesc, METH_VARARGS, "."},
	{"get_upnp_urls", (PyCFunction)_GetUPNPUrls, METH_VARARGS, "."},
	{NULL}
};

void
initupnp(void)
{
	Py_InitModule("upnp", upnp_methods);
}
