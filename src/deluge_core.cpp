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
#if defined(_WIN32)
# if defined(socklen_t)
#  undef socklen_t
# endif
#endif
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
#include "libtorrent/size_type.hpp"
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
#define EVENT_FILE_ERROR            4
#define EVENT_HASH_FAILED_ERROR     5
#define EVENT_PEER_BAN_ERROR        6
#define EVENT_FASTRESUME_REJECTED_ERROR 8
#define EVENT_TRACKER_ANNOUNCE      9
#define EVENT_TRACKER_REPLY         10
#define EVENT_TRACKER_ALERT         11
#define EVENT_TRACKER_WARNING       12
#define EVENT_OTHER                 13
#define EVENT_STORAGE_MOVED         14
#define EVENT_PIECE_FINISHED        15
#define EVENT_BLOCK_DOWNLOADING     16
#define EVENT_BLOCK_FINISHED        17
#define EVENT_PEER_BLOCKED          18

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
pe_settings    *M_pe_settings = NULL;
proxy_settings    *M_proxy_settings = NULL;
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
static PyObject *SystemError           = NULL;
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
        //            printf("Found: %li\r\n", i);
        return i;
    }

    RAISE_INT(DelugeError, "Handle not found.");
}

long get_index_from_unique_ID(long unique_ID)
{

    for (unsigned long i = 0; i < M_torrents->size(); i++)
        if ((*M_torrents)[i].unique_ID == unique_ID)
            return i;

    RAISE_INT(DelugeError, "No such unique_ID.");
}

partial_piece_info internal_get_piece_info(torrent_handle h, long piece_index)
{
    std::vector<partial_piece_info> queue;
    std::vector<partial_piece_info>& q = queue;
    h.get_download_queue(q);
    for (unsigned long i = 0; i < q.size(); i++)
    {
        if ((long)q[i].piece_index == piece_index) return queue[i];
    }
}

torrent_info internal_get_torrent_info(std::string const& torrent_name)
{
    std::ifstream in(torrent_name.c_str(), std::ios_base::binary);
    in.unsetf(std::ios_base::skipws);
    entry e;
    e = bdecode(std::istream_iterator<char>(in), std::istream_iterator<char>());

    torrent_info t(e);

    return t;
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

    torrent_handle h = M_ses->add_torrent(t, save_path, resume_data, compact_mode);
    //    h.set_max_connections(60); // at some point we should use this
    h.set_max_uploads(-1);
    h.set_ratio(preferred_ratio);
    h.resolve_countries(true);
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

bool internal_has_piece(std::vector<bool> const& pieces, long index)
{
    return pieces[index];
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
        
        num_peers = peers.size();
    }

    return num_peers;
}


//=====================
// External functions
//=====================

static PyObject *torrent_pre_init(PyObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, "OOOOOO", &DelugeError,
        &InvalidEncodingError,
        &SystemError,
        &FilesystemError,
        &DuplicateTorrentError,
        &InvalidTorrentError))
        return NULL;

    Py_INCREF(Py_None); return Py_None;
}


static PyObject *torrent_init(PyObject *self, PyObject *args)
{
    printf("deluge_core; using libtorrent %s. Compiled %s NDEBUG.\r\n",
        LIBTORRENT_VERSION,
#ifdef NDEBUG
  "with"
#else
  "without"
#endif
          );

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
#if defined(_WIN32)
    M_ses->set_max_half_open_connections(8);
#else
    M_ses->set_max_half_open_connections(-1);
#endif

    M_ses->set_download_rate_limit(-1);
    M_ses->set_upload_rate_limit(-1);

    M_ses->set_settings(*M_settings);
    M_ses->set_severity_level(alert::debug);

    M_ses->add_extension(&libtorrent::create_metadata_plugin);

    M_constants = Py_BuildValue("{s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i}",
        "EVENT_NULL",                         EVENT_NULL,
        "EVENT_FINISHED",                     EVENT_FINISHED,
        "EVENT_PEER_ERROR",                   EVENT_PEER_ERROR,
        "EVENT_INVALID_REQUEST",              EVENT_INVALID_REQUEST,
        "EVENT_FILE_ERROR",                   EVENT_FILE_ERROR,
        "EVENT_HASH_FAILED_ERROR",            EVENT_HASH_FAILED_ERROR,
        "EVENT_PEER_BAN_ERROR",               EVENT_PEER_BAN_ERROR,
        "EVENT_FASTRESUME_REJECTED_ERROR",    EVENT_FASTRESUME_REJECTED_ERROR,
        "EVENT_TRACKER_ANNOUNCE",             EVENT_TRACKER_ANNOUNCE,
        "EVENT_TRACKER_REPLY",                EVENT_TRACKER_REPLY,
        "EVENT_TRACKER_ALERT",                EVENT_TRACKER_ALERT,
        "EVENT_TRACKER_WARNING",              EVENT_TRACKER_WARNING,
        "EVENT_OTHER",                        EVENT_OTHER,
        "EVENT_STORAGE_MOVED",                EVENT_STORAGE_MOVED,
        "EVENT_PIECE_FINISHED",               EVENT_PIECE_FINISHED,
        "EVENT_BLOCK_DOWNLOADING",            EVENT_BLOCK_DOWNLOADING,
        "EVENT_BLOCK_FINISHED",               EVENT_BLOCK_FINISHED,
        "EVENT_PEER_BLOCKED",                 EVENT_PEER_BLOCKED,
        "STATE_QUEUED",                       STATE_QUEUED,
        "STATE_CHECKING",                     STATE_CHECKING,
        "STATE_CONNECTING",                   STATE_CONNECTING,
        "STATE_DOWNLOADING_META",             STATE_DOWNLOADING_META,
        "STATE_DOWNLOADING",                  STATE_DOWNLOADING,
        "STATE_FINISHED",                     STATE_FINISHED,
        "STATE_SEEDING",                      STATE_SEEDING,
        "STATE_ALLOCATING",                   STATE_ALLOCATING);

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

    M_ses->set_download_rate_limit(arg);
    Py_INCREF(Py_None); return Py_None;
}


static PyObject *torrent_set_upload_rate_limit(PyObject *self, PyObject *args)
{
    python_long arg;
    if (!PyArg_ParseTuple(args, "i", &arg))
        return NULL;

    M_ses->set_upload_rate_limit(arg);
    Py_INCREF(Py_None); return Py_None;
}

static PyObject *torrent_set_per_upload_rate_limit(PyObject *self, PyObject *args)
{
    python_long unique_ID, speed;
    if (!PyArg_ParseTuple(args, "ii", &unique_ID, &speed))
        return NULL;

    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;
        
    if (M_torrents->at(index).handle.is_valid())
        M_torrents->at(index).handle.set_upload_limit(speed);    

    Py_INCREF(Py_None); return Py_None;
}

static PyObject *torrent_get_per_upload_rate_limit(PyObject *self, PyObject *args)
{
    python_long unique_ID;
    if (!PyArg_ParseTuple(args, "i", &unique_ID))
        return NULL;

    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;
        
    if (M_torrents->at(index).handle.is_valid())
        return Py_BuildValue("i", (python_long)M_torrents->at(index).handle.upload_limit());
}

static PyObject *torrent_set_per_download_rate_limit(PyObject *self, PyObject *args)
{
    python_long unique_ID, speed;

    if (!PyArg_ParseTuple(args, "ii", &unique_ID, &speed))
        return NULL;
        
    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;
    if (M_torrents->at(index).handle.is_valid())
        M_torrents->at(index).handle.set_download_limit(speed);

    Py_INCREF(Py_None); return Py_None;
}

static PyObject *torrent_get_per_download_rate_limit(PyObject *self, PyObject *args)
{
    python_long unique_ID;

    if (!PyArg_ParseTuple(args, "i", &unique_ID))
        return NULL;
        
    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;
    if (M_torrents->at(index).handle.is_valid())
        return Py_BuildValue("i", (python_long)M_torrents->at(index).handle.download_limit());
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


static PyObject *torrent_set_max_upload_slots_global(PyObject *self, PyObject *args)
{
    python_long max_up;
    if (!PyArg_ParseTuple(args, "i", &max_up))
        return NULL;

    M_ses->set_max_uploads(max_up);

    Py_INCREF(Py_None); return Py_None;
}


static PyObject *torrent_set_max_connections_global(PyObject *self, PyObject *args)
{
    python_long max_conn;
    if (!PyArg_ParseTuple(args, "i", &max_conn))
        return NULL;

    //    printf("Setting max connections: %d\r\n", max_conn);
    M_ses->set_max_connections(max_conn);

    Py_INCREF(Py_None); return Py_None;
}

static PyObject *torrent_dump_file_info(PyObject *self, PyObject *args)
{
    const char *name;
    if (!PyArg_ParseTuple(args, "s", &name))
        return NULL;

    torrent_info t = internal_get_torrent_info(name);
    
    PyObject *file_info;
    long file_index = 0;
    PyObject *ret = PyTuple_New(t.num_files());

    for(torrent_info::file_iterator i = t.begin_files(); i != t.end_files(); ++i)
    {
        file_entry const &currFile = (*i);

        file_info = Py_BuildValue(
            "{s:s,s:L}",
            "path",     currFile.path.string().c_str(),
            "size",     currFile.size
            );
            
        PyTuple_SetItem(ret, file_index, file_info);   
        file_index++;
    };

    return ret;
}

static PyObject *torrent_dump_trackers(PyObject *self, PyObject *args)
{
    const char *name;
    if (!PyArg_ParseTuple(args, "s", &name))
        return NULL;

    torrent_info t = internal_get_torrent_info(name);
    std::string trackerslist;
    {
    for (std::vector<announce_entry>::const_iterator i = t.trackers().begin(); 
        i != t.trackers().end(); ++i)
        {
        trackerslist = trackerslist + i->url +"\n";
        }
    }
    return Py_BuildValue("s",trackerslist.c_str());
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
        long ret = internal_add_torrent(name, 1.0, compact, save_dir_2);
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

static PyObject *torrent_test_duplicate(PyObject *self, PyObject *args)
{
    const char *name;
    python_long unique_ID;
    if (!PyArg_ParseTuple(args, "si", &name, &unique_ID))
        return NULL;

    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    torrent_info t = internal_get_torrent_info(name);
    return Py_BuildValue("b", t.info_hash() == M_torrents->at(index).handle.info_hash());
    
}

static PyObject *torrent_move_storage(PyObject *self, PyObject *args)
{
    const char *move_dir;
    python_long unique_ID;
    if (!PyArg_ParseTuple(args, "is", &unique_ID, &move_dir))
        return NULL;

    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    boost::filesystem::path move_dir_2 (move_dir, empty_name_check);
    if (M_torrents->at(index).handle.is_valid())
        M_torrents->at(index).handle.move_storage(move_dir_2);
    Py_INCREF(Py_None); return Py_None;
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

static PyObject *torrent_has_piece(PyObject *self, PyObject *args)
{
    python_long unique_ID;
    long piece_index;
    bool has_piece;
    if (!PyArg_ParseTuple(args, "ii", &unique_ID, &piece_index))
        return NULL;

    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    torrent_status s = M_torrents->at(index).handle.status();
    if (s.pieces == 0)
        return Py_BuildValue("b", false);
    has_piece = internal_has_piece(*s.pieces, piece_index);
    return Py_BuildValue("b", has_piece);
}

static PyObject *torrent_get_all_piece_info(PyObject *self, PyObject *args)
{
   python_long unique_ID;
    if (!PyArg_ParseTuple(args, "i", &unique_ID))
        return NULL;

    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    torrent_handle h = M_torrents->at(index).handle;
    std::vector<partial_piece_info> queue;
    std::vector<partial_piece_info>& q = queue;
    h.get_download_queue(q);    
    PyObject *piece_info;
    long piece_index = 0;
    PyObject *ret = PyTuple_New(q.size());

    for(unsigned long i=0; i<q.size(); i++)
    {
        piece_info = Py_BuildValue("{s:i,s:i,s:i}",
            "piece_index", q[i].piece_index,
            "blocks_total", q[i].blocks_in_piece,
            "blocks_finished", q[i].finished);
            
        PyTuple_SetItem(ret, piece_index, piece_info);   
        piece_index++;
    };
    return ret;
}

static PyObject *torrent_get_piece_info(PyObject *self, PyObject *args)
{
    python_long unique_ID;
    long piece_index;
    if (!PyArg_ParseTuple(args, "ii", &unique_ID, &piece_index))
        return NULL;

    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    torrent_handle h = M_torrents->at(index).handle;
    partial_piece_info piece_info = internal_get_piece_info(h, piece_index);
    int blocks_total=0, blocks_finished=0;
    if(piece_info.piece_index == piece_index) 
    {
        blocks_total = piece_info.blocks_in_piece;
        blocks_finished = piece_info.finished;
    }
    return Py_BuildValue("{s:i,s:i}",
        "blocks_total", blocks_total,
        "blocks_finished", blocks_finished);
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

    long connected_seeds = 0;
    long connected_peers = 0;
    long total_seeds = 0;
    long total_peers = 0;

    connected_peers = s.num_peers - s.num_seeds;
    connected_seeds = s.num_seeds;

    total_seeds = s.num_complete != -1? s.num_complete : connected_seeds;
    total_peers = s.num_incomplete != -1? s.num_incomplete : connected_peers;


    return Py_BuildValue("{s:s,s:i,s:i,s:l,s:l,s:f,s:f,s:b,s:f,s:L,s:L,s:s,s:s,s:f,s:L,s:L,s:l,s:i,s:i,s:L,s:L,s:i,s:l,s:l,s:b,s:b,s:L,s:L,s:L}",
        "name",               t.handle.get_torrent_info().name().c_str(),
        "num_files",          t.handle.get_torrent_info().num_files(),
        "state",              s.state,
        "num_peers",          connected_peers,
        "num_seeds",          connected_seeds,
        "distributed_copies", s.distributed_copies == -1.0 ? 0.0 : s.distributed_copies,
        "download_rate",      s.download_payload_rate,
        "compact_mode",       s.compact_mode,
        "upload_rate",        s.upload_payload_rate,
        "total_download",     s.total_download,
        "total_upload",       s.total_upload,
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
    "total_seeds",          total_seeds,
        "is_paused",          t.handle.is_paused(),
        "is_seed",            t.handle.is_seed(),
        "total_done",          s.total_done,
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
    } else if (dynamic_cast<peer_blocked_alert*>(popped_alert))
    {
        std::string peer_IP =
            (dynamic_cast<peer_blocked_alert*>(popped_alert))->ip.to_string();
        return Py_BuildValue("{s:i,s:s,s:s}", 
            "event_type", EVENT_PEER_BLOCKED,
            "ip", peer_IP.c_str(),
            "message", a->msg().c_str());
    } else if (dynamic_cast<block_downloading_alert*>(popped_alert))
    {
        torrent_handle handle = (dynamic_cast<block_downloading_alert*>(popped_alert))->handle;
        int piece_index = (dynamic_cast<block_downloading_alert*>(popped_alert))->piece_index;
        int block_index = (dynamic_cast<block_downloading_alert*>(popped_alert))->block_index;
        std::string speedmsg = (dynamic_cast<block_downloading_alert*>(popped_alert))->peer_speedmsg;
        long index = get_torrent_index(handle);
        if (PyErr_Occurred())
            return NULL;

        if (handle_exists(handle))
            return Py_BuildValue("{s:i,s:i,s:i,s:i,s:s,s:s}", 
                "event_type", EVENT_BLOCK_DOWNLOADING,
                "unique_ID", M_torrents->at(index).unique_ID,
                "block_index", block_index,
                "piece_index", piece_index,
                "peer_speed", speedmsg.c_str(),
                "message", a->msg().c_str());
        else
            { Py_INCREF(Py_None); return Py_None; }
    } else if (dynamic_cast<block_finished_alert*>(popped_alert))
    {
        torrent_handle handle = (dynamic_cast<block_finished_alert*>(popped_alert))->handle;
        int piece_index = (dynamic_cast<block_finished_alert*>(popped_alert))->piece_index;
        int block_index = (dynamic_cast<block_finished_alert*>(popped_alert))->block_index;
        long index = get_torrent_index(handle);
        if (PyErr_Occurred())
            return NULL;

        if (handle_exists(handle))
            return Py_BuildValue("{s:i,s:i,s:i,s:i,s:s}", 
                "event_type", EVENT_BLOCK_FINISHED,
                "unique_ID", M_torrents->at(index).unique_ID,
                "block_index", block_index,
                "piece_index", piece_index,
                "message", a->msg().c_str());
        else
            { Py_INCREF(Py_None); return Py_None; }
    } else if (dynamic_cast<piece_finished_alert*>(popped_alert))
    {
        torrent_handle handle = (dynamic_cast<piece_finished_alert*>(popped_alert))->handle;
        int piece_index = (dynamic_cast<piece_finished_alert*>(popped_alert))->piece_index;
        long index = get_torrent_index(handle);
        if (PyErr_Occurred())
            return NULL;

        if (handle_exists(handle))
            return Py_BuildValue("{s:i,s:i,s:i,s:s}", 
                "event_type", EVENT_PIECE_FINISHED,
                "unique_ID", M_torrents->at(index).unique_ID,
                "piece_index", piece_index,
                "message", a->msg().c_str());
        else
            { Py_INCREF(Py_None); return Py_None; }
    } else if (dynamic_cast<torrent_finished_alert*>(popped_alert))
    {
        torrent_handle handle = (dynamic_cast<torrent_finished_alert*>(popped_alert))->handle;

        long index = get_torrent_index(handle);
        if (PyErr_Occurred())
            return NULL;

        if (handle_exists(handle))
            return Py_BuildValue("{s:i,s:i,s:s}", 
                "event_type", EVENT_FINISHED,
                "unique_ID", M_torrents->at(index).unique_ID,
                "message", a->msg().c_str());
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
            return Py_BuildValue("{s:i,s:i,s:s}",
                "event_type",       EVENT_TRACKER_ANNOUNCE,
                "unique_ID",
                M_torrents->at(index).unique_ID,
                "message",          a->msg().c_str());
        else
            { Py_INCREF(Py_None); return Py_None; }
    } else if (dynamic_cast<tracker_alert*>(popped_alert))
    {
        torrent_handle handle = (dynamic_cast<tracker_alert*>(popped_alert))->handle;
        long index = get_torrent_index(handle);
        if (PyErr_Occurred())
            return NULL;
        int status_code = (dynamic_cast<tracker_alert*>(popped_alert))->status_code;
        int times_in_row = (dynamic_cast<tracker_alert*>(popped_alert))->times_in_row;

        if (handle_exists(handle))
            return Py_BuildValue("{s:i,s:i,s:i,s:i,s:s}",
                "event_type",       EVENT_TRACKER_ALERT,
                "unique_ID",
                M_torrents->at(index).unique_ID,
                "status_code",      status_code,
                "times_in_row",     times_in_row,
                "message",          a->msg().c_str());
        else
            { Py_INCREF(Py_None); return Py_None; }
    } else if (dynamic_cast<storage_moved_alert*>(popped_alert))
    {
        torrent_handle handle = (dynamic_cast<storage_moved_alert*>(popped_alert))->handle;
        long index = get_torrent_index(handle);
        if (PyErr_Occurred())
            return NULL;

        if (handle_exists(handle))
            return Py_BuildValue("{s:i,s:i,s:s}",
                "event_type",       EVENT_STORAGE_MOVED,
                "unique_ID",        M_torrents->at(index).unique_ID,
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
            return Py_BuildValue("{s:i,s:i,s:s}",
                "event_type",       EVENT_TRACKER_REPLY,
                "unique_ID",
                M_torrents->at(index).unique_ID,
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
            return Py_BuildValue("{s:i,s:i,s:s}",
                "event_type",       EVENT_TRACKER_WARNING,
                "unique_ID",
                M_torrents->at(index).unique_ID,
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

    return Py_BuildValue("{s:l,s:f,s:f,s:l,s:f,s:f}",
        "has_incoming_connections", long(s.has_incoming_connections),
        "upload_rate",          float(s.payload_upload_rate),
        "download_rate",        float(s.payload_download_rate),
        "num_peers",            long(s.num_peers),
        "total_downloaded",     float(s.total_payload_download),
        "total_uploaded",       float(s.total_payload_upload));
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

        std::stringstream country;
        country << peers[i].country[0] << peers[i].country[1];

        peer_info = Py_BuildValue(
            "{s:f,s:L,s:f,s:L,s:i,s:i,s:b,s:b,s:b,s:b,s:b,s:b,s:b,s:b,s:b,s:s,s:b,s:s,s:f,s:O,s:b,s:b,s:s}",
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
            "plaintext_encrypted",   ((peers[i].flags & peer_info::plaintext_encrypted) != 0),
            "country",               country.str().c_str()
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
            "{s:s,s:L,s:f}",
            "path",     currFile.path.string().c_str(),
            "size",     currFile.size,
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

static PyObject *torrent_get_file_piece_range(PyObject *self, PyObject *args)
{
    python_long unique_ID;
    if (!PyArg_ParseTuple(args, "i", &unique_ID))
        return NULL;

    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    std::vector<PyObject *> temp_files;

    torrent_info const &info = M_torrents->at(index).handle.get_torrent_info();
    int file_index = 0;
    size_type first_num_blocks, last_num_blocks;
    PyObject *file_info;

    for(torrent_info::file_iterator i = info.begin_files(); i != info.end_files(); ++i)
    {
        file_entry const &currFile = (*i);
        peer_request first_index = info.map_file(file_index, 0, 1);
        peer_request last_index = info.map_file(file_index, currFile.size-1, 1);
        first_num_blocks = info.piece_length()/(16 * 1024);
        last_num_blocks = ceil((double)(info.piece_size(last_index.piece))/(16 * 1024));
        file_info = Py_BuildValue(
            "{s:i,s:i,s:i,s:i,s:s}",
            "first_index",     first_index.piece,
            "last_index",      last_index.piece,
            "first_num_blocks", (int)first_num_blocks,
            "last_num_blocks", (int)last_num_blocks,
            "path",            currFile.path.string().c_str()
            );
        file_index++;
        temp_files.push_back(file_info);
    };

    PyObject *ret = PyTuple_New(temp_files.size());

    for (unsigned long i = 0; i < temp_files.size(); i++)
        PyTuple_SetItem(ret, i, temp_files[i]);

    return ret;
};

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

    //    printf("Loading DHT state from %s\r\n", DHT_path);

    boost::filesystem::path tempPath(DHT_path, empty_name_check);
    boost::filesystem::ifstream DHT_state_file(tempPath, std::ios_base::binary);
    DHT_state_file.unsetf(std::ios_base::skipws);

    entry DHT_state;
    try
    {
        DHT_state = bdecode(std::istream_iterator<char>(DHT_state_file),
            std::istream_iterator<char>());
        M_ses->start_dht(DHT_state);
        //        printf("DHT state recovered.\r\n");

        //        // Print out the state data from the FILE (not the session!)
        //        printf("Number of DHT peers in recovered state: %ld\r\n", count_DHT_peers(DHT_state));

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

    //    printf("Saving DHT state to %s\r\n", DHT_path);

    boost::filesystem::path tempPath = boost::filesystem::path(DHT_path, empty_name_check);

    try
    {
        entry DHT_state = M_ses->dht_state();

        //        printf("Number of DHT peers in state, saving: %ld\r\n", count_DHT_peers(DHT_state));

        boost::filesystem::ofstream out(tempPath, std::ios_base::binary);
        out.unsetf(std::ios_base::skipws);
        bencode(std::ostream_iterator<char>(out), DHT_state);
    }
    catch (std::exception& e)
    {
        printf("An error occured in saving DHT\r\n");
        std::cerr << e.what() << "\n";
    }
    
    M_ses->stop_dht();

    Py_INCREF(Py_None); return Py_None;
}


static PyObject *torrent_get_DHT_info(PyObject *self, PyObject *args)
{
    entry DHT_state = M_ses->dht_state();

    return Py_BuildValue("l", python_long(count_DHT_peers(DHT_state)));

    /*
    //    DHT_state.print(cout);
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

    //path::default_name_check(no_check);

    char *destination, *comment, *creator_str, *input, *trackers;
    bool *priv;
    python_long piece_size;
    if (!PyArg_ParseTuple(args, "ssssisb",
        &destination, &input, &trackers, &comment, &piece_size, &creator_str, &priv))
        return NULL;

    piece_size = piece_size * 1024;

    try
    {
		boost::intrusive_ptr<torrent_info> t(new torrent_info);
        boost::filesystem::path full_path = complete(boost::filesystem::path(input));
        boost::filesystem::ofstream out(complete(boost::filesystem::path(destination)), std::ios_base::binary);


        internal_add_files(*t, full_path.branch_path(), full_path.leaf());
		t->set_piece_size(piece_size);

        file_pool fp;
        boost::scoped_ptr<storage_interface> st(default_storage_constructor(t, full_path.branch_path(), fp));

        std::string stdTrackers(trackers);
        unsigned long index = 0, next = stdTrackers.find("\n");
        while (1 == 1)
        {
            t->add_tracker(stdTrackers.substr(index, next-index));
            index = next + 1;
            if (next >= stdTrackers.length())
                break;
            next = stdTrackers.find("\n", index);
            if (next == std::string::npos)
                break;
        }

        int num = t->num_pieces();
        std::vector<char> buf(piece_size);
        for (int i = 0; i < num; ++i)
        {
            st->read(&buf[0], i, 0, t->piece_size(i));
            hasher h(&buf[0], t->piece_size(i));
            t->set_hash(i, h.final());
        }

        t->set_creator(creator_str);
        t->set_comment(comment);
        t->set_priv(priv);
        entry e = t->create_torrent();
        bencode(std::ostream_iterator<char>(out), e);
        return Py_BuildValue("l", 1);
    } catch (std::exception& e)
    {
        //        std::cerr << e.what() << "\n";
        //        return Py_BuildValue("l", 0);
        RAISE_PTR(DelugeError, e.what());
        return Py_BuildValue("l", 0);
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

static PyObject *torrent_set_IP_filter(PyObject *self, PyObject *args)
{
    if (M_the_filter == NULL) {
        RAISE_PTR(DelugeError, "No filter defined, use reset_IP_filter");
    }
    M_ses->set_ip_filter(*M_the_filter);

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
    libtorrent::pe_settings::enc_level    level;
    
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
    python_long unique_ID;
    float num;
    if (!PyArg_ParseTuple(args, "if", &unique_ID, &num))
        return NULL;
    
    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    M_torrents->at(index).handle.set_ratio(num);
    
    Py_INCREF(Py_None); return Py_None;
}

static PyObject *torrent_proxy_settings(PyObject *self, PyObject *args)
{
    char *server, *login, *pasw;
    int portnum;
    libtorrent::proxy_settings::proxy_type proxytype;
    char *dtpwproxy;

    PyArg_ParseTuple(args, "sssiis", &server, &login, &pasw, &portnum, 
                                     &proxytype, &dtpwproxy);
    
    M_proxy_settings = new proxy_settings();
    M_proxy_settings->type = proxytype;
    M_proxy_settings->username = login;
    M_proxy_settings->password = pasw;
    M_proxy_settings->hostname = server;
    M_proxy_settings->port = portnum;
    
    if (strcmp(dtpwproxy, "peer") == 0) {
        M_ses->set_peer_proxy(*M_proxy_settings);
    }

    if (strcmp(dtpwproxy, "tracker") == 0) {
        M_ses->set_tracker_proxy(*M_proxy_settings);
    }

    if (strcmp(dtpwproxy, "dht") == 0) {
        M_ses->set_dht_proxy(*M_proxy_settings);
    }
    if (strcmp(dtpwproxy, "web") == 0) {
        M_ses->set_web_seed_proxy(*M_proxy_settings);
    }

    return Py_None;
}

static PyObject *torrent_get_trackers(PyObject *self, PyObject *args)
{
    python_long unique_ID;
    if (!PyArg_ParseTuple(args, "i", &unique_ID))
        return NULL;

    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    torrent_handle& h = M_torrents->at(index).handle;
    std::string trackerslist;
    if (h.is_valid() && h.has_metadata())
        {
        for (std::vector<announce_entry>::const_iterator i = h.trackers().begin(); 
            i != h.trackers().end(); ++i)
            {
            trackerslist = trackerslist + i->url +"\n";
            }
        }
    return Py_BuildValue("s",trackerslist.c_str());
}

static PyObject *torrent_replace_trackers(PyObject *self, PyObject *args)
{
  python_long unique_ID;
  const char* tracker;
  if (!PyArg_ParseTuple(args, "iz", &unique_ID, &tracker))
    return NULL;
  long index = get_index_from_unique_ID(unique_ID);
  if (PyErr_Occurred())
    return NULL;

  torrent_handle& h = M_torrents->at(index).handle;

  std::vector<libtorrent::announce_entry> trackerlist;
    
  std::istringstream trackers(tracker);
  std::string line;
    
  while (std::getline(trackers, line)) {
    libtorrent::announce_entry a_entry(line);
    trackerlist.push_back(a_entry);
  }
  h.replace_trackers(trackerlist);
  h.force_reannounce();
  return Py_None;
}
static PyObject *torrent_prioritize_files(PyObject *self, PyObject *args)
{
    python_long unique_ID;
    PyObject *priorities_list_object;
    
    if (!PyArg_ParseTuple(args, "iO", &unique_ID, &priorities_list_object))
        return NULL;
    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    torrent_t &t = M_torrents->at(index);
    int num_files = t.handle.get_torrent_info().num_files();
    assert(PyList_Size(priorities_list_object) == num_files);

    std::vector<int> priorities_vector(num_files);
    
    for (long i = 0; i < num_files; i++) {
        priorities_vector.at(i) = 
            PyInt_AsLong(PyList_GetItem(priorities_list_object, i));
    }

    t.handle.prioritize_files(priorities_vector);

    #ifndef NDEBUG
    int num_pieces = t.handle.get_torrent_info().num_pieces();
    
    std::vector<int> priorities_pieces_vector(num_pieces);
    priorities_pieces_vector = t.handle.piece_priorities();
    
    std::cout << "after files prioritization\n";
    for (long i = 0; i < num_pieces; i++) {
        std::cout << priorities_pieces_vector.at(i);
    }
    std::cout << "\n";
    #endif
    
    return Py_None;
}

static PyObject *torrent_prioritize_first_last_pieces(PyObject *self, 
                                                      PyObject *args)
{
#define FIRST_LAST_PRIO 6
    
    // Prioritize first and last 1% of file size bytes in each file of torrent
    // with unique_ID
    python_long unique_ID;
    PyObject *priorities_list_object;
    
    // We need priorities_list_object to see whether file is marked to 
    // download(has priority > 0) or not.
    if (!PyArg_ParseTuple(args, "iO", &unique_ID, &priorities_list_object))
        return NULL;
    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    torrent_t &t = M_torrents->at(index);
    const torrent_info &tor_info = t.handle.get_torrent_info();
    int num_files = tor_info.num_files();
    assert(PyList_Size(priorities_list_object) == num_files);
    int num_pieces = tor_info.num_pieces();

    std::vector<int> priorities_vector(num_pieces);
    priorities_vector = t.handle.piece_priorities();
    
    #ifndef NDEBUG
    std::cout << "priority distribution in torrent_prioritize_first_last_pieces()\n";
    std::cout << "before prioritization\n";
    for (long i = 0; i < num_pieces; i++) {
        std::cout << priorities_vector.at(i);
    }
    std::cout << "\n";
    #endif
        
    for (long i = 0; i < num_files; i++) {
        file_entry const &file = tor_info.file_at(i);
        if(file.size == 0) {
            continue;
        }

        // Check if file has priority 0 - means don't download - skip it 
        // and move to next file
        int file_prio = PyInt_AsLong(PyList_GetItem(priorities_list_object, 
                                                    i));
        if(file_prio == 0) {
            continue;
        }        
            
        int start_piece = tor_info.map_file(i, 0, 0).piece;
        int end_piece = tor_info.map_file(i, file.size, 0).piece;
        if (end_piece == num_pieces)
            end_piece -= 1;
        // Set prio_size to 1% of the file size
        size_type prio_size = file.size / 100;
        int prio_pieces = tor_info.map_file(i, prio_size, 0).piece -
                              start_piece + 1;
        
        #ifndef NDEBUG
        std::cout << "s=" << start_piece << ", e=" << end_piece << ", p=" << prio_pieces << "\n";
        #endif
        
        for (int piece = 0; piece < prio_pieces; piece++) {
            priorities_vector.at(start_piece + piece) = FIRST_LAST_PRIO; 
            priorities_vector.at(end_piece - piece) = FIRST_LAST_PRIO; 
        }
    }

    t.handle.prioritize_pieces(priorities_vector);
        
    #ifndef NDEBUG
    std::cout << "after prioritization\n";
    for (long i = 0; i < num_pieces; i++) {
        std::cout << priorities_vector.at(i);
    }
    std::cout << "\n";
    #endif

    return Py_None;
}


static PyObject *torrent_set_priv(PyObject *self, PyObject *args)
{
    using namespace libtorrent;
    python_long unique_ID;
    bool onoff;
    
    if (!PyArg_ParseTuple(args, "ib", &unique_ID, &onoff))
        return NULL;
    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    torrent_t &t = M_torrents->at(index);
    torrent_info info = t.handle.get_torrent_info();

    info.set_priv(onoff);

    return Py_None;
}

static PyObject *torrent_set_max_connections_per_torrent(PyObject *self, PyObject *args)
{
    python_long unique_ID, max_connections;
    
    if (!PyArg_ParseTuple(args, "ii", &unique_ID, &max_connections))
        return NULL;
    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    torrent_t &t = M_torrents->at(index);
    t.handle.set_max_connections(max_connections);

    return Py_None;
}

static PyObject *torrent_set_max_upload_slots_per_torrent(PyObject *self, PyObject *args)
{
    python_long unique_ID, max_upload_slots;
    
    if (!PyArg_ParseTuple(args, "ii", &unique_ID, &max_upload_slots))
        return NULL;
    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    torrent_t &t = M_torrents->at(index);
    t.handle.set_max_uploads(max_upload_slots);

    return Py_None;
}

static PyObject *torrent_add_url_seed(PyObject *self, PyObject *args)
{
    python_long unique_ID;
    char *address;
    
    if (!PyArg_ParseTuple(args, "is", &unique_ID, &address))
        return NULL;
    long index = get_index_from_unique_ID(unique_ID);
    if (PyErr_Occurred())
        return NULL;

    torrent_t &t = M_torrents->at(index);
    t.handle.add_url_seed(address);
    return Py_None;
}

//====================
// Python Module data
//====================

static PyMethodDef deluge_core_methods[] =
{
    {"add_url_seed",                    torrent_add_url_seed,                      METH_VARARGS,   "."},
    {"pe_settings",                     torrent_pe_settings,                      METH_VARARGS,   "."},
    {"pre_init",                        torrent_pre_init,                         METH_VARARGS,   "."},
    {"init",                            torrent_init,                             METH_VARARGS,   "."},
    {"quit",                            torrent_quit,                             METH_VARARGS,   "."},
    {"save_fastresume",                 torrent_save_fastresume,                  METH_VARARGS,   "."},
    {"set_max_half_open",               torrent_set_max_half_open,                METH_VARARGS,   "."},
    {"set_download_rate_limit",         torrent_set_download_rate_limit,          METH_VARARGS,   "."},
    {"set_upload_rate_limit",           torrent_set_upload_rate_limit,            METH_VARARGS,   "."},
    {"set_per_upload_rate_limit",       torrent_set_per_upload_rate_limit,        METH_VARARGS,   "."},
    {"set_per_download_rate_limit",     torrent_set_per_download_rate_limit,      METH_VARARGS,   "."},
    {"get_per_upload_rate_limit",       torrent_get_per_upload_rate_limit,        METH_VARARGS,   "."},
    {"get_per_download_rate_limit",     torrent_get_per_download_rate_limit,      METH_VARARGS,   "."},
    {"set_listen_on",                   torrent_set_listen_on,                    METH_VARARGS,   "."},
    {"is_listening",                    torrent_is_listening,                     METH_VARARGS,   "."},
    {"listening_port",                  torrent_listening_port,                   METH_VARARGS,   "."},
    {"set_max_upload_slots_global",     torrent_set_max_upload_slots_global,      METH_VARARGS,   "."},
    {"set_max_upload_slots_per_torrent",torrent_set_max_upload_slots_per_torrent, METH_VARARGS,   "."},
    {"set_max_connections_global",      torrent_set_max_connections_global,       METH_VARARGS,   "."},
    {"set_max_connections_per_torrent", torrent_set_max_connections_per_torrent,  METH_VARARGS,   "."},
    {"add_torrent",                     torrent_add_torrent,                      METH_VARARGS,   "."},
    {"move_storage",                    torrent_move_storage,                     METH_VARARGS,   "."},
    {"remove_torrent",                  torrent_remove_torrent,                   METH_VARARGS,   "."},
    {"get_num_torrents",                torrent_get_num_torrents,                 METH_VARARGS,   "."},
    {"reannounce",                      torrent_reannounce,                       METH_VARARGS,   "."},
    {"pause",                           torrent_pause,                            METH_VARARGS,   "."},
    {"resume",                          torrent_resume,                           METH_VARARGS,   "."},
    {"get_torrent_state",               torrent_get_torrent_state,                METH_VARARGS,   "."},
    {"pop_event",                       torrent_pop_event,                        METH_VARARGS,   "."},
    {"get_session_info",                torrent_get_session_info,                 METH_VARARGS,   "."},
    {"get_peer_info",                   torrent_get_peer_info,                    METH_VARARGS,   "."},
    {"get_file_info",                   torrent_get_file_info,                    METH_VARARGS,   "."},
    {"dump_file_info",                  torrent_dump_file_info,                   METH_VARARGS,   "."},
    {"constants",                       torrent_constants,                        METH_VARARGS,   "."},
    {"start_DHT",                       torrent_start_DHT,                        METH_VARARGS,   "."},
    {"stop_DHT",                        torrent_stop_DHT,                         METH_VARARGS,   "."},
    {"get_DHT_info",                    torrent_get_DHT_info,                     METH_VARARGS,   "."},
    {"create_torrent",                  torrent_create_torrent,                   METH_VARARGS,   "."},
    {"reset_IP_filter",                 torrent_reset_IP_filter,                  METH_VARARGS,   "."},
    {"add_range_to_IP_filter",          torrent_add_range_to_IP_filter,           METH_VARARGS,   "."},
    {"set_IP_filter",                   torrent_set_IP_filter,                    METH_VARARGS,   "."},
    {"use_upnp",                        torrent_use_upnp,                         METH_VARARGS,   "."},
    {"use_natpmp",                      torrent_use_natpmp,                       METH_VARARGS,   "."},
    {"use_utpex",                       torrent_use_utpex,                        METH_VARARGS,   "."},
    {"set_ratio",                       torrent_set_ratio,                        METH_VARARGS,   "."},
    {"proxy_settings",                  torrent_proxy_settings,                   METH_VARARGS,   "."},
    {"get_trackers",                    torrent_get_trackers,                     METH_VARARGS,   "."},
    {"dump_trackers",                   torrent_dump_trackers,                    METH_VARARGS,   "."},
    {"replace_trackers",                torrent_replace_trackers,                 METH_VARARGS,   "."},
    {"prioritize_files",                torrent_prioritize_files,                 METH_VARARGS,   "."},
    {"prioritize_first_last_pieces",    torrent_prioritize_first_last_pieces,     METH_VARARGS,   "."},
    {"set_priv",                        torrent_set_priv,                         METH_VARARGS,   "."},
    {"test_duplicate",                  torrent_test_duplicate,                   METH_VARARGS,   "."},
    {"has_piece",                       torrent_has_piece,                        METH_VARARGS,   "."},
    {"get_piece_info",                  torrent_get_piece_info,                   METH_VARARGS,   "."},
    {"get_all_piece_info",              torrent_get_all_piece_info,               METH_VARARGS,   "."},
    {"get_file_piece_range",            torrent_get_file_piece_range,             METH_VARARGS,   "."},
    {NULL}
};

PyMODINIT_FUNC
initdeluge_core(void)
{
    Py_InitModule("deluge_core", deluge_core_methods);
};
