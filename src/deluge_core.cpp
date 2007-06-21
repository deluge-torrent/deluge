/*
 *  Copyright  2006 Alon Zakai ('Kripken') <kripkensteiner@gmail.com>
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2, or (at your option)
 *  any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 *
 *   In addition, as a special exception, the copyright holders give
 *  permission to link the code of portions of this program with the OpenSSL
 *  library.
 *  You must obey the GNU General Public License in all respects for all of
 *  the code used other than OpenSSL. If you modify file(s) with this
 *  exception, you may extend this exception to your version of the file(s),
 *  but you are not obligated to do so. If you do not wish to do so, delete
 *  this exception statement from your version. If you delete this exception
 *  statement from all source files in the program, then also delete it here.
 *
 *  Thank You: Some code portions were derived from BSD-licensed work by
 *             Arvid Norberg, and GPL-licensed work by Christophe Dumez
 */

//------------------
// TODO:
//
// The DHT capability requires UDP. We need to check that this port is in fact
// open, just like the normal TCP port for bittorrent.
//
//-----------------
#include <Python.h>

#include <boost/filesystem/exception.hpp>
#include <boost/filesystem/operations.hpp>
#include <boost/date_time/posix_time/posix_time.hpp>

#include "libtorrent/entry.hpp"
#include "libtorrent/bencode.hpp"
#include "libtorrent/session.hpp"
#include "libtorrent/identify_client.hpp"
#include "libtorrent/alert_types.hpp"
#include "libtorrent/storage.hpp"
#include "libtorrent/hasher.hpp"
#include "libtorrent/ip_filter.hpp"
#include "libtorrent/upnp.hpp"
#include "libtorrent/file_pool.hpp"
#include "libtorrent/natpmp.hpp"
#include "libtorrent/extensions/metadata_transfer.hpp"
#include "libtorrent/extensions/ut_pex.hpp"

using namespace boost::filesystem;
using namespace libtorrent;

//----------------
// CONSTANTS
//----------------

#ifdef AMD64
#define python_long int
#else
#define python_long long
#endif

#define EVENT_NULL                  0
#define EVENT_FINISHED              1
#define EVENT_PEER_ERROR            2
#define EVENT_INVALID_REQUEST       3
#define EVENT_FILE_ERROR        4
#define EVENT_HASH_FAILED_ERROR     5
#define EVENT_PEER_BAN_ERROR        6
#define EVENT_FASTRESUME_REJECTED_ERROR 8
#define EVENT_TRACKER           9
#define EVENT_OTHER         10

#define STATE_QUEUED                0
#define STATE_CHECKING              1
#define STATE_CONNECTING            2
#define STATE_DOWNLOADING_META      3
#define STATE_DOWNLOADING           4
#define STATE_FINISHED              5
#define STATE_SEEDING               6
#define STATE_ALLOCATING            7

#define DHT_ROUTER_PORT         6881

//-----------------
// TYPES
//-----------------

typedef long          unique_ID_t;
typedef std::vector<bool> filter_out_t;
typedef std::string   torrent_name_t;

struct torrent_t
{
    torrent_handle handle;
    unique_ID_t    unique_ID;
};

typedef std::vector<torrent_t> torrents_t;
typedef torrents_t::iterator   torrents_t_iterator;

//---------------------------
// MODULE-GLOBAL VARIABLES
//---------------------------

long          M_unique_counter  = 0;
session_settings *M_settings        = NULL;
pe_settings	*M_pe_settings = NULL;
proxy_settings	*M_proxy_settings = NULL;
session          *M_ses         = NULL;
PyObject         *M_constants       = NULL;
ip_filter    *M_the_filter      = NULL;
torrents_t       *M_torrents        = NULL;

//------------------------
// Exception types & macro
//------------------------

static PyObject *DelugeError           = NULL;
static PyObject *InvalidEncodingError  = NULL;
static PyObject *FilesystemError       = NULL;
static PyObject *DuplicateTorrentError = NULL;
static PyObject *InvalidTorrentError   = NULL;

#define RAISE_PTR(e,s) { printf("Raising error: %s\r\n", s); PyErr_SetString(e, s); return NULL; }
#define RAISE_INT(e,s) { printf("Raising error: %s\r\n", s); PyErr_SetString(e, s); return -1; }

//---------------------
// Internal functions
//---------------------

bool empty_name_check(const std::string & name)
{
    return 1;
}


long handle_exists(torrent_handle &handle)
{
    for (unsigned long i = 0; i < M_torrents->size(); i++)
        if ((*M_torrents)[i].handle == handle)
            return 1;

    return 0;
}


long get_torrent_index(torrent_handle &handle)
{
    for (unsigned long i = 0; i < M_torrents->size(); i++)
        if ((*M_torrents)[i].handle == handle)
    {
        //			printf("Found: %li\r\n", i);
        return i;
    }

    RAISE_INT(DelugeError, "Handle not found.");
}


long get_index_from_unique_ID(long unique_ID)
{
    assert(M_handles->size() == M_unique_IDs->size());

    for (unsigned long i = 0; i < M_torrents->size(); i++)
        if ((*M_torrents)[i].unique_ID == unique_ID)
            return i;

    RAISE_INT(DelugeError, "No such unique_ID.");
}


long internal_add_torrent(std::string const&    torrent_name,
float   preferred_ratio,
bool    compact_mode,
boost::filesystem::path const& save_path)
{

    std::ifstream in(torrent_name.c_str(), std::ios_base::binary);
    in.unsetf(std::ios_base::skipws);
    entry e;
    e = bdecode(std::istream_iterator<char>(in), std::istream_iterator<char>());

    torrent_info t(e);

    entry resume_data;
    try
    {
        std::stringstream s;
        s << torrent_name << ".fastresume";
        boost::filesystem::ifstream resumeFile(s.str(), std::ios_base::binary);
        resumeFile.unsetf(std::ios_base::skipws);
        resume_data = bdecode(std::istream_iterator<char>(resumeFile),
            std::istream_iterator<char>());
    }
    catch (invalid_encoding&)
    {
    }
    catch (boost::filesystem::filesystem_error&) {}

    // Create new torrent object

    torrent_t new_torrent;

    torrent_handle h = M_ses->add_torrent(t, save_path, resume_data, compact_mode, 16 * 1024);
    //	h.set_max_connections(60); // at some point we should use this
    h.set_max_uploads(-1);
    h.set_ratio(preferred_ratio);
    new_torrent.handle = h;

    new_torrent.unique_ID = M_unique_counter;
    M_unique_counter++;

    M_torrents->push_back(new_torrent);

    return (new_torrent.unique_ID);
}


void internal_remove_torrent(long index)
{
    assert(index < M_torrents->size());

    torrent_handle& h = M_torrents->at(index).handle;

    M_ses->remove_torrent(h);

    torrents_t_iterator it = M_torrents->begin() + index;
    M_torrents->erase(it);
}


long get_peer_index(tcp::endpoint addr, std::vector<peer_info> const& peers)
{
    long index = -1;

    for (unsigned long i = 0; i < peers.size(); i++)
        if (peers[i].ip == addr)
            index = i;

    return index;
}


// The following function contains code by Christophe Dumez and Arvid Norberg
void internal_add_files(torrent_info&   t,
boost::filesystem::path const& p,
boost::filesystem::path const& l)
{
                                 // change default checker, perhaps?
    boost::filesystem::path f(p / l);
    if (is_directory(f))
    {
        for (boost::filesystem::directory_iterator i(f), end; i != end; ++i)
            internal_add_files(t, p, l / i->leaf());
    } else
    t.add_file(l, file_size(f));
}


long count_DHT_peers(entry &state)
{
    long num_peers = 0;
    entry *nodes = state.find_key("nodes");
    if (nodes)
    {
        entry::list_type &peers = nodes->list();
        entry::list_type::const_iterator i;
        i = peers.begin();

        while (i != peers.end())
        {
            num_peers++;
            i++;
        }
    }

    return num_peers;
}


//=====================
// External functions
//=====================

static PyObject *torrent_pre_init(PyObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, "OOOOO", &DelugeError,
        &InvalidEncodingError,
        &FilesystemError,
        &DuplicateTorrentError,
        &InvalidTorrentError))
        return NULL;

    Py_INCREF(Py_None); return Py_None;
}


static PyObject *torrent_init(PyObject *self, PyObject *args)
{
    printf("deluge_core; using libtorrent %s. Compiled with NDEBUG value: %d\r\n",
        LIBTORRENT_VERSION,
        NDEBUG);

    // Tell Boost that we are on *NIX, so bloody '.'s are ok inside a directory name!
    boost::filesystem::path::default_name_check(empty_name_check);

    char *client_ID, *user_agent;
    python_long v1,v2,v3,v4;

    if (!PyArg_ParseTuple(args, "siiiis", &client_ID, &v1, &v2, &v3, &v4, &user_agent))
        return NULL;

    M_settings  = new session_settings;
    M_ses       = new session(fingerprint(client_ID, v1, v2, v3, v4));

    M_torrents  = new torrents_t;
    M_torrents->reserve(10);     // pretty cheap, just 10

    // Init values

    M_settings->user_agent = std::string(user_agent);

    M_ses->set_max_half_open_connections(-1);
    M_ses->set_download_rate_limit(-1);
    M_ses->set_upload_rate_limit(-1);

    M_ses->set_settings(*M_settings);
    M_ses->set_severity_level(alert::debug);

    M_ses->add_extension(&libtorrent::create_metadata_plugin);

    M_constants = Py_BuildValue("{s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i}",
        "EVENT_NULL",               EVENT_NULL,
        "EVENT_FINISHED",           EVENT_FINISHED,
        "EVENT_PEER_ERROR",         EVENT_PEER_ERROR,
        "EVENT_INVALID_REQUEST",        EVENT_INVALID_REQUEST,
        "EVENT_FILE_ERROR",         EVENT_FILE_ERROR,
        "EVENT_HASH_FAILED_ERROR",      EVENT_HASH_FAILED_ERROR,
        "EVENT_PEER_BAN_ERROR",         EVENT_PEER_BAN_ERROR,
        "EVENT_FASTRESUME_REJECTED_ERROR",  EVENT_FASTRESUME_REJECTED_ERROR,
        "EVENT_TRACKER",            EVENT_TRACKER,
        "EVENT_OTHER",              EVENT_OTHER,
        "STATE_QUEUED",             STATE_QUEUED,
        "STATE_CHECKING",           STATE_CHECKING,
        "STATE_CONNECTING",         STATE_CONNECTING,
        "STATE_DOWNLOADING_META",       STATE_DOWNLOADING_META,
        "STATE_DOWNLOADING",            STATE_DOWNLOADING,
        "STATE_FINISHED",           STATE_FINISHED,
        "STATE_SEEDING",            STATE_SEEDING,
        "STATE_ALLOCATING",         STATE_ALLOCATING);

    Py_INCREF(Py_None); return Py_None;
};

static PyObject *torrent_quit(PyObject *self, PyObject *args)
{
    M_settings->stop_tracker_timeout = 5;
    M_ses->set_settings(*M_settings);
    printf("core: removing torrents...\r\n");
    delete M_torrents;
    printf("core: removing settings...\r\n");
    delete M_settings;
    printf("core: shutting down session...\r\n");
    delete M_ses;                // 100% CPU...
    Py_DECREF(M_constants);

    printf("core shut down.\r\n");

    Py_INCREF(Py_None); return Py_None;
};

static PyObject *torrent_save_fastresume(PyObject *self, PyObject *args)
{
    python_long unique_ID;
    const char *torrent_name;
    if (!PyArg_ParseTuple(args, "is", &unique_ID, &torrent_name))
        return NULL;

    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    torrent_handle& h = M_torrents->at(index).handle;
    // For valid torrents, save fastresume data
    if (h.is_valid() && h.has_metadata())
    {
        h.pause();

        entry data = h.write_resume_data();

        std::stringstream s;
        s << torrent_name << ".fastresume";

        boost::filesystem::ofstream out(s.str(), std::ios_base::binary);

        out.unsetf(std::ios_base::skipws);

        bencode(std::ostream_iterator<char>(out), data);

        h.resume();

        Py_INCREF(Py_None); return Py_None;
    } else
    RAISE_PTR(DelugeError, "Invalid handle or no metadata for fastresume.");
}


static PyObject *torrent_set_max_half_open(PyObject *self, PyObject *args)
{
    python_long arg;
    if (!PyArg_ParseTuple(args, "i", &arg))
        return NULL;

    M_ses->set_max_half_open_connections(arg);

    Py_INCREF(Py_None); return Py_None;
}


static PyObject *torrent_set_download_rate_limit(PyObject *self, PyObject *args)
{
    python_long arg;
    if (!PyArg_ParseTuple(args, "i", &arg))
        return NULL;

    //	printf("Capping download to %d bytes per second\r\n", (int)arg);
    M_ses->set_download_rate_limit(arg);

    Py_INCREF(Py_None); return Py_None;
}


static PyObject *torrent_set_upload_rate_limit(PyObject *self, PyObject *args)
{
    python_long arg;
    if (!PyArg_ParseTuple(args, "i", &arg))
        return NULL;

    //	printf("Capping upload to %d bytes per second\r\n", (int)arg);
    M_ses->set_upload_rate_limit(arg);

    Py_INCREF(Py_None); return Py_None;
}


static PyObject *torrent_set_listen_on(PyObject *self, PyObject *args)
{
    PyObject *port_vec;
    if (!PyArg_ParseTuple(args, "O", &port_vec))
        return NULL;

    M_ses->listen_on(std::make_pair( PyInt_AsLong(PyList_GetItem(port_vec, 0)),
        PyInt_AsLong(PyList_GetItem(port_vec, 1))), "");

    Py_INCREF(Py_None); return Py_None;
}


static PyObject *torrent_is_listening(PyObject *self, PyObject *args)
{
    long ret = (M_ses->is_listening() != 0);

    return Py_BuildValue("i", ret);
}


static PyObject *torrent_listening_port(PyObject *self, PyObject *args)
{
    return Py_BuildValue("i", (python_long)M_ses->listen_port());
}


static PyObject *torrent_set_max_uploads(PyObject *self, PyObject *args)
{
    python_long max_up;
    if (!PyArg_ParseTuple(args, "i", &max_up))
        return NULL;

    M_ses->set_max_uploads(max_up);

    Py_INCREF(Py_None); return Py_None;
}


static PyObject *torrent_set_max_connections(PyObject *self, PyObject *args)
{
    python_long max_conn;
    if (!PyArg_ParseTuple(args, "i", &max_conn))
        return NULL;

    //	printf("Setting max connections: %d\r\n", max_conn);
    M_ses->set_max_connections(max_conn);

    Py_INCREF(Py_None); return Py_None;
}


static PyObject *torrent_add_torrent(PyObject *self, PyObject *args)
{
    const char *name, *save_dir;
    python_long compact;
    if (!PyArg_ParseTuple(args, "ssi", &name, &save_dir, &compact))
        return NULL;

    boost::filesystem::path save_dir_2  (save_dir, empty_name_check);
    try
    {
        long ret = internal_add_torrent(name, 0, compact, save_dir_2);
        if (PyErr_Occurred())
            return NULL;
        else
            return Py_BuildValue("i", ret);
    }
    catch (invalid_encoding&)
        {   RAISE_PTR(InvalidEncodingError, ""); }
    catch (invalid_torrent_file&)
        {   RAISE_PTR(InvalidTorrentError, ""); }
    catch (boost::filesystem::filesystem_error&)
        {   RAISE_PTR(FilesystemError, ""); }
    catch (duplicate_torrent&)
        {   RAISE_PTR(DuplicateTorrentError, "libtorrent reports this is a duplicate torrent"); }
}


static PyObject *torrent_remove_torrent(PyObject *self, PyObject *args)
{
    python_long unique_ID;
    if (!PyArg_ParseTuple(args, "i", &unique_ID))
        return NULL;

    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    internal_remove_torrent(index);

    Py_INCREF(Py_None); return Py_None;
}


static PyObject *torrent_get_num_torrents(PyObject *self, PyObject *args)
{
    return Py_BuildValue("i", M_torrents->size());
}


static PyObject *torrent_reannounce(PyObject *self, PyObject *args)
{
    python_long unique_ID;
    if (!PyArg_ParseTuple(args, "i", &unique_ID))
        return NULL;

    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    M_torrents->at(index).handle.force_reannounce();

    Py_INCREF(Py_None); return Py_None;
}


static PyObject *torrent_pause(PyObject *self, PyObject *args)
{
    python_long unique_ID;
    if (!PyArg_ParseTuple(args, "i", &unique_ID))
        return NULL;
    
    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    M_torrents->at(index).handle.pause();
    
    Py_INCREF(Py_None); return Py_None;
}


static PyObject *torrent_resume(PyObject *self, PyObject *args)
{
    python_long unique_ID;
    if (!PyArg_ParseTuple(args, "i", &unique_ID))
        return NULL;

    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    M_torrents->at(index).handle.resume();

    Py_INCREF(Py_None); return Py_None;
}


static PyObject *torrent_get_torrent_state(PyObject *self, PyObject *args)
{
    python_long unique_ID;
    if (!PyArg_ParseTuple(args, "i", &unique_ID))
        return NULL;

    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    torrent_t               &t = M_torrents->at(index);
    torrent_status           s = t.handle.status();
    const torrent_info  &i = t.handle.get_torrent_info();

    std::vector<peer_info> peers;
    t.handle.get_peer_info(peers);

    long connected_seeds = 0;
    long connected_peers = 0;
    long total_seeds = 0;
    long total_peers = 0;
    
    for (unsigned long i = 0; i < peers.size(); i++) {

			connected_peers = s.num_peers - s.num_seeds;

			connected_seeds = s.num_seeds;

			total_seeds = s.num_complete != -1? s.num_complete : connected_seeds;
			
			total_peers = s.num_incomplete != -1? s.num_incomplete : connected_peers;
		}

    return Py_BuildValue("{s:s,s:i,s:i,s:l,s:l,s:f,s:f,s:f,s:L,s:L,s:b,s:s,s:s,s:f,s:L,s:L,s:l,s:i,s:i,s:L,s:L,s:i,s:l,s:l,s:b,s:b,s:L,s:L,s:L}",
        "name",               t.handle.get_torrent_info().name().c_str(),
        "num_files",          t.handle.get_torrent_info().num_files(),
        "state",              s.state,
        "num_peers",          connected_peers,
        "num_seeds",          connected_seeds,
        "distributed_copies", s.distributed_copies,
        "download_rate",      s.download_rate,
        "upload_rate",        s.upload_rate,
        "total_download",     s.total_download,
        "total_upload",       s.total_upload,
        "tracker_ok",         !s.current_tracker.empty(),
        "next_announce",      boost::posix_time::to_simple_string(s.next_announce).c_str(),
        "tracker",            s.current_tracker.c_str(),
        "progress",           s.progress,
        "total_payload_download", s.total_payload_download,
        "total_payload_upload", s.total_payload_upload,
        "pieces",             long(s.pieces), // this is really a std::vector<bool>*
        "pieces_done",        s.num_pieces,
        "block_size",         s.block_size,
        "total_size",         i.total_size(),
        "piece_length",       i.piece_length(),
        "num_pieces",         i.num_pieces(),
	"total_peers",        total_peers,
	"total_seeds",	      total_seeds,
        "is_paused",          t.handle.is_paused(),
        "is_seed",            t.handle.is_seed(),
        "total_done",	      s.total_done,
        "total_wanted",       s.total_wanted,
        "total_wanted_done",  s.total_wanted_done);
};

static PyObject *torrent_pop_event(PyObject *self, PyObject *args)
{
    std::auto_ptr<alert> a;

    a = M_ses->pop_alert();

    alert *popped_alert = a.get();

    if (!popped_alert)
    {
        Py_INCREF(Py_None); return Py_None;
    } else if (dynamic_cast<torrent_finished_alert*>(popped_alert))
    {
        torrent_handle handle = (dynamic_cast<torrent_finished_alert*>(popped_alert))->handle;

        long index = get_torrent_index(handle);
        if (PyErr_Occurred())
            return NULL;

        if (handle_exists(handle))
            return Py_BuildValue("{s:i,s:i}", "event_type", EVENT_FINISHED,
                "unique_ID",
                M_torrents->at(index).unique_ID);
        else
            { Py_INCREF(Py_None); return Py_None; }
    } else if (dynamic_cast<peer_error_alert*>(popped_alert))
    {
        peer_id     peer_ID = (dynamic_cast<peer_error_alert*>(popped_alert))->pid;
        std::string peer_IP =
            (dynamic_cast<peer_error_alert*>(popped_alert))->ip.address().to_string();

        return Py_BuildValue("{s:i,s:s,s:s,s:s}",   "event_type",   EVENT_PEER_ERROR,
            "client_ID",    identify_client(peer_ID).c_str(),
            "ip",       peer_IP.c_str(),
            "message",  a->msg().c_str());
    } else if (dynamic_cast<invalid_request_alert*>(popped_alert))
    {
        peer_id peer_ID = (dynamic_cast<invalid_request_alert*>(popped_alert))->pid;

        return Py_BuildValue("{s:i,s:s,s:s}",
            "event_type", EVENT_INVALID_REQUEST,
            "client_ID",  identify_client(peer_ID).c_str(),
            "message",   a->msg().c_str());
    } else if (dynamic_cast<file_error_alert*>(popped_alert))
    {
        torrent_handle handle = (dynamic_cast<file_error_alert*>(popped_alert))->handle;
        long index = get_torrent_index(handle);
        if (PyErr_Occurred())
            return NULL;

        if (handle_exists(handle))
            return Py_BuildValue("{s:i,s:i,s:s}",
                "event_type", EVENT_FILE_ERROR,
                "unique_ID", M_torrents->at(index).unique_ID,
                "message",   a->msg().c_str());
        else
            { Py_INCREF(Py_None); return Py_None; }
    } else if (dynamic_cast<hash_failed_alert*>(popped_alert))
    {
        torrent_handle handle = (dynamic_cast<hash_failed_alert*>(popped_alert))->handle;
        long index = get_torrent_index(handle);
        if (PyErr_Occurred())
            return NULL;

        if (handle_exists(handle))
            return Py_BuildValue("{s:i,s:i,s:i,s:s}",
                "event_type",  EVENT_HASH_FAILED_ERROR,
                "unique_ID",  M_torrents->at(index).unique_ID,
                "piece_index",
                long((dynamic_cast<hash_failed_alert*>(popped_alert))->piece_index),
                "message",    a->msg().c_str());
        else
            { Py_INCREF(Py_None); return Py_None; }
    } else if (dynamic_cast<peer_ban_alert*>(popped_alert))
    {
        torrent_handle handle = (dynamic_cast<peer_ban_alert*>(popped_alert))->handle;
        long index = get_torrent_index(handle);
        if (PyErr_Occurred())
            return NULL;
        std::string peer_IP = (dynamic_cast<peer_ban_alert*>(popped_alert))->ip.address().to_string();

        if (handle_exists(handle))
            return Py_BuildValue("{s:i,s:i,s:s,s:s}",
                "event_type", EVENT_PEER_BAN_ERROR,
                "unique_ID",  M_torrents->at(index).unique_ID,
                "ip",         peer_IP.c_str(),
                "message",    a->msg().c_str());
        else
            { Py_INCREF(Py_None); return Py_None; }
    } else if (dynamic_cast<fastresume_rejected_alert*>(popped_alert))
    {
        torrent_handle handle = (dynamic_cast<fastresume_rejected_alert*>(popped_alert))->handle;
        long index = get_torrent_index(handle);
        if (PyErr_Occurred())
            return NULL;

        if (handle_exists(handle))
            return Py_BuildValue("{s:i,s:i,s:s}",
                "event_type",  EVENT_FASTRESUME_REJECTED_ERROR,
                "unique_ID",  M_torrents->at(index).unique_ID,
                "message",    a->msg().c_str());
        else
            { Py_INCREF(Py_None); return Py_None; }
    } else if (dynamic_cast<tracker_announce_alert*>(popped_alert))
    {
        torrent_handle handle = (dynamic_cast<tracker_announce_alert*>(popped_alert))->handle;
        long index = get_torrent_index(handle);
        if (PyErr_Occurred())
            return NULL;

        if (handle_exists(handle))
            return Py_BuildValue("{s:i,s:i,s:s,s:s}",
                "event_type",       EVENT_TRACKER,
                "unique_ID",
                M_torrents->at(index).unique_ID,
                "tracker_status",   "Announce sent",
                "message",          a->msg().c_str());
        else
            { Py_INCREF(Py_None); return Py_None; }
    } else if (dynamic_cast<tracker_alert*>(popped_alert))
    {
        torrent_handle handle = (dynamic_cast<tracker_alert*>(popped_alert))->handle;
        long index = get_torrent_index(handle);
        if (PyErr_Occurred())
            return NULL;

        if (handle_exists(handle))
            return Py_BuildValue("{s:i,s:i,s:s,s:s}",
                "event_type",       EVENT_TRACKER,
                "unique_ID",
                M_torrents->at(index).unique_ID,
                "tracker_status",   "Bad response (status code=?)",
                "message",          a->msg().c_str());
        else
            { Py_INCREF(Py_None); return Py_None; }
    } else if (dynamic_cast<tracker_reply_alert*>(popped_alert))
    {
        torrent_handle handle = (dynamic_cast<tracker_reply_alert*>(popped_alert))->handle;
        long index = get_torrent_index(handle);
        if (PyErr_Occurred())
            return NULL;

        if (handle_exists(handle))
            return Py_BuildValue("{s:i,s:i,s:s,s:s}",
                "event_type",       EVENT_TRACKER,
                "unique_ID",
                M_torrents->at(index).unique_ID,
                "tracker_status",   "Announce succeeded",
                "message",          a->msg().c_str());
        else
            { Py_INCREF(Py_None); return Py_None; }
    } else if (dynamic_cast<tracker_warning_alert*>(popped_alert))
    {
        torrent_handle handle = (dynamic_cast<tracker_warning_alert*>(popped_alert))->handle;
        long index = get_torrent_index(handle);
        if (PyErr_Occurred())
            return NULL;

        if (handle_exists(handle))
            return Py_BuildValue("{s:i,s:i,s:s,s:s}",
                "event_type",       EVENT_TRACKER,
                "unique_ID",
                M_torrents->at(index).unique_ID,
                "tracker_status",   "Warning in response",
                "message",          a->msg().c_str());
        else
            { Py_INCREF(Py_None); return Py_None; }
    }

    return Py_BuildValue("{s:i,s:s}", "event_type", EVENT_OTHER,
        "message",   a->msg().c_str()     );
}


static PyObject *torrent_get_session_info(PyObject *self, PyObject *args)
{
    session_status s = M_ses->status();

    return Py_BuildValue("{s:l,s:f,s:f,s:f,s:f,s:l}",
        "has_incoming_connections", long(s.has_incoming_connections),
        "upload_rate",          float(s.upload_rate),
        "download_rate",        float(s.download_rate),
        "payload_upload_rate",      float(s.payload_upload_rate),
        "payload_download_rate",    float(s.payload_download_rate),
        "num_peers",            long(s.num_peers));
}


static PyObject *torrent_get_peer_info(PyObject *self, PyObject *args)
{
    python_long unique_ID;
    if (!PyArg_ParseTuple(args, "i", &unique_ID))
        return NULL;

    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    std::vector<peer_info> peers;
    M_torrents->at(index).handle.get_peer_info(peers);

    PyObject *peer_info;
    PyObject *ret = PyTuple_New(peers.size());
    PyObject *curr_piece, *py_pieces;

    for (unsigned long i = 0; i < peers.size(); i++)
    {
        std::vector<bool> &pieces      = peers[i].pieces;
        unsigned long      pieces_had  = 0;

        py_pieces = PyTuple_New(pieces.size());

        for (unsigned long piece = 0; piece < pieces.size(); piece++)
        {
            if (pieces[piece])
                pieces_had++;

            curr_piece = Py_BuildValue("i", long(pieces[piece]));
            PyTuple_SetItem(py_pieces, piece, curr_piece);
        }

        peer_info = Py_BuildValue(
            "{s:f,s:L,s:f,s:L,s:i,s:i,s:b,s:b,s:b,s:b,s:b,s:b,s:b,s:b,s:b,s:s,s:b,s:s,s:f,s:O,s:b,s:b}",
            "download_speed",        peers[i].down_speed,
            "total_download",        peers[i].total_download,
            "upload_speed",          peers[i].up_speed,
            "total_upload",          peers[i].total_upload,
            "download_queue_length", peers[i].download_queue_length,
            "upload_queue_length",   peers[i].upload_queue_length,
            "is_interesting",        ((peers[i].flags & peer_info::interesting) != 0),
            "is_choked",             ((peers[i].flags & peer_info::choked) != 0),
            "is_remote_interested",  ((peers[i].flags & peer_info::remote_interested) != 0),
            "is_remote_choked",      ((peers[i].flags & peer_info::remote_choked) != 0),
            "supports_extensions",   ((peers[i].flags & peer_info::supports_extensions) != 0),
            "is_local_connection",   ((peers[i].flags & peer_info::local_connection) != 0),
            "is_awaiting_handshake", ((peers[i].flags & peer_info::handshake) != 0),
            "is_connecting",         ((peers[i].flags & peer_info::connecting) != 0),
            "is_queued",             ((peers[i].flags & peer_info::queued) != 0),
            "client",                peers[i].client.c_str(),
            "is_seed",               ((peers[i].flags & peer_info::seed) != 0),
            "ip",                    peers[i].ip.address().to_string().c_str(),
            "peer_has",              float(float(pieces_had)*100.0/pieces.size()),
            "pieces",                py_pieces,
            "rc4_encrypted",         ((peers[i].flags & peer_info::rc4_encrypted) != 0),
            "plaintext_encrypted",   ((peers[i].flags & peer_info::plaintext_encrypted) != 0)
            );

        Py_DECREF(py_pieces);    // Assuming the previous line does NOT steal the ref, then this is
        // needed!

        PyTuple_SetItem(ret, i, peer_info);
    };

    return ret;
};

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

    for(torrent_info::file_iterator i = start; i != end; ++i)
    {
        file_entry const &currFile = (*i);

        file_info = Py_BuildValue(
            "{s:s,s:d,s:d,s:f}",
            "path",     currFile.path.string().c_str(),
            "offset",   double(currFile.offset),
            "size",     double(currFile.size),
            "progress", progresses[i - start]*100.0
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

    filter_out_t filter_out(num_files);

    for (long i = 0; i < num_files; i++)
    {
        filter_out.at(i) =
            PyInt_AsLong(PyList_GetItem(filter_out_object, i));
    };

    t.handle.filter_files(filter_out);

    Py_INCREF(Py_None); return Py_None;
}


/*static PyObject *torrent_get_unique_IDs(PyObject *self, PyObject *args)
{
    PyObject *ret = PyTuple_New(M_torrents.size());
    PyObject *temp;

    for (unsigned long i = 0; i < M_torrents.size(); i++)
    {
        temp = Py_BuildValue("i", M_torrents->at(i).unique_ID)

        PyTuple_SetItem(ret, i, temp);
    };

    return ret;
};*/

static PyObject *torrent_constants(PyObject *self, PyObject *args)
{
    Py_INCREF(M_constants); return M_constants;
}


static PyObject *torrent_start_DHT(PyObject *self, PyObject *args)
{
    const char *DHT_path;
    if (!PyArg_ParseTuple(args, "s", &DHT_path))
        return NULL;

    //	printf("Loading DHT state from %s\r\n", DHT_path);

    boost::filesystem::path tempPath(DHT_path, empty_name_check);
    boost::filesystem::ifstream DHT_state_file(tempPath, std::ios_base::binary);
    DHT_state_file.unsetf(std::ios_base::skipws);

    entry DHT_state;
    try
    {
        DHT_state = bdecode(std::istream_iterator<char>(DHT_state_file),
            std::istream_iterator<char>());
        M_ses->start_dht(DHT_state);
        //		printf("DHT state recovered.\r\n");

        //		// Print out the state data from the FILE (not the session!)
        //		printf("Number of DHT peers in recovered state: %ld\r\n", count_DHT_peers(DHT_state));

    }
    catch (std::exception&)
    {
        printf("No DHT file to resume\r\n");
        M_ses->start_dht();
    }

    M_ses->add_dht_router(std::make_pair(std::string("router.bittorrent.com"),
        DHT_ROUTER_PORT));
    M_ses->add_dht_router(std::make_pair(std::string("router.utorrent.com"),
        DHT_ROUTER_PORT));
    M_ses->add_dht_router(std::make_pair(std::string("router.bitcomet.com"),
        DHT_ROUTER_PORT));

    Py_INCREF(Py_None); return Py_None;
}


static PyObject *torrent_stop_DHT(PyObject *self, PyObject *args)
{
    const char *DHT_path;
    if (!PyArg_ParseTuple(args, "s", &DHT_path))
        return NULL;

    //	printf("Saving DHT state to %s\r\n", DHT_path);

    boost::filesystem::path tempPath = boost::filesystem::path(DHT_path, empty_name_check);

    try
    {
        entry DHT_state = M_ses->dht_state();

        //		printf("Number of DHT peers in state, saving: %ld\r\n", count_DHT_peers(DHT_state));

        boost::filesystem::ofstream out(tempPath, std::ios_base::binary);
        out.unsetf(std::ios_base::skipws);
        bencode(std::ostream_iterator<char>(out), DHT_state);
    }
    catch (std::exception& e)
    {
        printf("An error occured in saving DHT\r\n");
        std::cerr << e.what() << "\n";
    }

    Py_INCREF(Py_None); return Py_None;
}


static PyObject *torrent_get_DHT_info(PyObject *self, PyObject *args)
{
    entry DHT_state = M_ses->dht_state();

    return Py_BuildValue("l", python_long(count_DHT_peers(DHT_state)));

    /*
    //	DHT_state.print(cout);
        entry *nodes = DHT_state.find_key("nodes");
        if (!nodes)
            return Py_BuildValue("l", -1); // No nodes - we are just starting up...

        entry::list_type &peers = nodes->list();
        entry::list_type::const_iterator i;

        python_long num_peers = 0;

        i = peers.begin();
        while (i != peers.end())
        {
            num_peers++;
            i++;
        }

        return Py_BuildValue("l", num_peers);
    */
}


// Create Torrents: call with something like:
// create_torrent("mytorrent.torrent", "directory or file to make a torrent out of",
//                "tracker1\ntracker2\ntracker3", "no comment", 256, "Deluge");
// That makes a torrent with pieces of 256K, with "Deluge" as the creator string.
//
// The following function contains code by Christophe Dumez and Arvid Norberg
static PyObject *torrent_create_torrent(PyObject *self, PyObject *args)
{
    using namespace libtorrent;
    using namespace boost::filesystem;

    path::default_name_check(no_check);

    char *destination, *comment, *creator_str, *input, *trackers;
    python_long piece_size;
    if (!PyArg_ParseTuple(args, "ssssis",
        &destination, &input, &trackers, &comment, &piece_size, &creator_str))
        return NULL;

    piece_size = piece_size * 1024;

    try
    {
        torrent_info t;
        boost::filesystem::path full_path = complete(boost::filesystem::path(input));
        boost::filesystem::ofstream out(complete(boost::filesystem::path(destination)), std::ios_base::binary);

        internal_add_files(t, full_path.branch_path(), full_path.leaf());
        t.set_piece_size(piece_size);

        file_pool fp;
        boost::scoped_ptr<storage_interface> st(
            default_storage_constructor(t, full_path.branch_path(), fp));

        std::string stdTrackers(trackers);
        unsigned long index = 0, next = stdTrackers.find("\n");
        while (1 == 1)
        {
            t.add_tracker(stdTrackers.substr(index, next-index));
            index = next + 1;
            if (next >= stdTrackers.length())
                break;
            next = stdTrackers.find("\n", index);
            if (next == std::string::npos)
                break;
        }

        int num = t.num_pieces();
        std::vector<char> buf(piece_size);
        for (int i = 0; i < num; ++i)
        {
            st->read(&buf[0], i, 0, t.piece_size(i));
            hasher h(&buf[0], t.piece_size(i));
            t.set_hash(i, h.final());
        }

        t.set_creator(creator_str);
        t.set_comment(comment);

        entry e = t.create_torrent();
        bencode(std::ostream_iterator<char>(out), e);
        return Py_BuildValue("l", 1);
    } catch (std::exception& e)
    {
        //		std::cerr << e.what() << "\n";
        //		return Py_BuildValue("l", 0);
        RAISE_PTR(DelugeError, e.what());
    }
}


static PyObject *torrent_reset_IP_filter(PyObject *self, PyObject *args)
{
    // Remove existing filter, if there is one
    if (M_the_filter != NULL)
        delete M_the_filter;

    M_the_filter = new ip_filter();

    M_ses->set_ip_filter(*M_the_filter);

    Py_INCREF(Py_None); return Py_None;
}


static PyObject *torrent_add_range_to_IP_filter(PyObject *self, PyObject *args)
{
    if (M_the_filter == NULL) {
        RAISE_PTR(DelugeError, "No filter defined, use reset_IP_filter");
    }

    char *start, *end;
    if (!PyArg_ParseTuple(args, "ss", &start, &end))
        return NULL;

    address_v4 inet_start = address_v4::from_string(start);
    address_v4 inet_end = address_v4::from_string(end);
    M_the_filter->add_rule(inet_start, inet_end, ip_filter::blocked);

    Py_INCREF(Py_None); return Py_None;
}

static PyObject *torrent_use_upnp(PyObject *self, PyObject *args)
{
	python_long action;
	PyArg_ParseTuple(args, "i", &action);

	if (action){
		M_ses->start_upnp();
	}
	else{
		M_ses->stop_upnp();
	}

    Py_INCREF(Py_None); return Py_None;

}

static PyObject *torrent_use_natpmp(PyObject *self, PyObject *args)
{
	python_long action;

	PyArg_ParseTuple(args, "i", &action);

	if (action){
		M_ses->start_natpmp();
	}
	else{
		M_ses->stop_natpmp();
	}

    Py_INCREF(Py_None); return Py_None;
}

static PyObject *torrent_use_utpex(PyObject *self, PyObject *args)
{
	python_long action;

	PyArg_ParseTuple(args, "i", &action);

	if (action){
		M_ses->add_extension(&libtorrent::create_ut_pex_plugin);
	}

    Py_INCREF(Py_None); return Py_None;
}

static PyObject *torrent_pe_settings(PyObject *self, PyObject *args)
{
	M_pe_settings = new pe_settings();
	libtorrent::pe_settings::enc_policy out, in, prefer;
	libtorrent::pe_settings::enc_level	level;
	
	PyArg_ParseTuple(args, "iiii", &out, &in, &level, &prefer);
	
	M_pe_settings->out_enc_policy = out;
	M_pe_settings->in_enc_policy = in;
	M_pe_settings->allowed_enc_level = level;
	M_pe_settings->prefer_rc4 = prefer;

	M_ses->set_pe_settings(*M_pe_settings);
	
	return Py_None;
}

static PyObject *torrent_set_ratio(PyObject *self, PyObject *args)
{
    python_long unique_ID, num;
    if (!PyArg_ParseTuple(args, "ii", &unique_ID, &num))
        return NULL;
    
    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    M_torrents->at(index).handle.set_ratio(num);
    
    Py_INCREF(Py_None); return Py_None;
}

static PyObject *torrent_proxy_settings(PyObject *self, PyObject *args)
{
	M_proxy_settings = new proxy_settings();

	char *server, *login, *pasw;
	int portnum;
	libtorrent::proxy_settings::proxy_type	proxytype;
	bool peerproxy, webseedproxy, trackerproxy, dhtproxy;

	PyArg_ParseTuple(args, "sssii", &server, &login, &pasw, &portnum, &proxytype, &peerproxy, &webseedproxy, &trackerproxy, &dhtproxy);
    
	M_proxy_settings->type = proxytype;
	M_proxy_settings->username = login;
	M_proxy_settings->password = pasw;
	M_proxy_settings->hostname = server;
	M_proxy_settings->port = portnum;
	
	if (peerproxy){
	M_ses->set_peer_proxy(*M_proxy_settings)
	}

	if (webseedproxy){
	M_ses->set_web_seed_proxy(*M_proxy_settings)
	}

	if (trackerproxy){
	M_ses->set_tracker_proxy(*M_proxy_settings)
	}

	if (dhtproxy){
	M_ses->set_dht_proxy(*M_proxy_settings)
	}

	Py_INCREF(Py_None); return Py_None;
}


//====================
// Python Module data
//====================

static PyMethodDef deluge_core_methods[] =
{
    {"pe_settings",                torrent_pe_settings,           METH_VARARGS,   "."},
    {"pre_init",                torrent_pre_init,           METH_VARARGS,   "."},
    {"init",                    torrent_init,               METH_VARARGS,   "."},
    {"quit",                    torrent_quit,               METH_VARARGS,   "."},
    {"save_fastresume",     torrent_save_fastresume,        METH_VARARGS,   "."},
    {"set_max_half_open",       torrent_set_max_half_open,      METH_VARARGS,   "."},
    {"set_download_rate_limit", torrent_set_download_rate_limit,    METH_VARARGS,   "."},
    {"set_upload_rate_limit",   torrent_set_upload_rate_limit,      METH_VARARGS,   "."},
    {"set_listen_on",           torrent_set_listen_on,              METH_VARARGS,   "."},
    {"is_listening",        torrent_is_listening,       METH_VARARGS,   "."},
    {"listening_port",      torrent_listening_port,     METH_VARARGS,   "."},
    {"set_max_uploads",         torrent_set_max_uploads,            METH_VARARGS,   "."},
    {"set_max_connections",     torrent_set_max_connections,        METH_VARARGS,   "."},
    {"add_torrent",             torrent_add_torrent,                METH_VARARGS,   "."},
    {"remove_torrent",          torrent_remove_torrent,             METH_VARARGS,   "."},
    {"get_num_torrents",        torrent_get_num_torrents,           METH_VARARGS,   "."},
    {"reannounce",              torrent_reannounce,                 METH_VARARGS,   "."},
    {"pause",                   torrent_pause,                      METH_VARARGS,   "."},
    {"resume",                  torrent_resume,                     METH_VARARGS,   "."},
    {"get_torrent_state",       torrent_get_torrent_state,          METH_VARARGS,   "."},
    {"pop_event",               torrent_pop_event,                  METH_VARARGS,   "."},
    {"get_session_info",        torrent_get_session_info,   METH_VARARGS,       "."},
    {"get_peer_info",       torrent_get_peer_info,      METH_VARARGS,   "."},
    {"get_file_info",       torrent_get_file_info,      METH_VARARGS,   "."},
    {"set_filter_out",      torrent_set_filter_out,         METH_VARARGS,   "."},
    {"constants",           torrent_constants,          METH_VARARGS,   "."},
    {"start_DHT",           torrent_start_DHT,          METH_VARARGS,   "."},
    {"stop_DHT",            torrent_stop_DHT,           METH_VARARGS,   "."},
    {"get_DHT_info",        torrent_get_DHT_info,       METH_VARARGS,   "."},
    {"create_torrent",      torrent_create_torrent,         METH_VARARGS,   "."},
    {"reset_IP_filter",     torrent_reset_IP_filter,        METH_VARARGS,   "."},
    {"add_range_to_IP_filter", torrent_add_range_to_IP_filter,    METH_VARARGS,   "."},
    {"use_upnp",                torrent_use_upnp,               METH_VARARGS,   "."},
    {"use_natpmp",              torrent_use_natpmp,               METH_VARARGS,   "."},
    {"use_utpex",                torrent_use_utpex,               METH_VARARGS,   "."},
    {"set_ratio",                torrent_set_ratio,               METH_VARARGS,   "."},
    {"proxy_settings",     torrent_proxy_settings,               METH_VARARGS,   "."},
    {NULL}
};

PyMODINIT_FUNC
initdeluge_core(void)
{
    Py_InitModule("deluge_core", deluge_core_methods);
};
