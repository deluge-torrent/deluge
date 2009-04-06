/*
Script: deluge-menus.js
    Contains the layout for all the popup menus used within the ajax ui.

 *
 * Copyright (C) Damien Churchill 2008 <damoxc@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, write to:
 *     The Free Software Foundation, Inc.,
 *     51 Franklin Street, Fifth Floor
 *     Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

 *
*/

Deluge.Menus = {
    Torrents: [
        {
            type:'text',
            action:'pause',
            text: _('Pause'),
            icon:'/static/images/16/pause.png'
        },
        {
            type: 'text',
            action: 'resume',
            text: _('Resume'),
            icon: '/static/images/16/start.png'
        },
        { type: 'seperator' },
        {
            type:'submenu',
            text: _('Options'),
            icon:'/static/images/16/preferences-system.png',
            items: [
                {
                    type: 'submenu',
                    text: _('D/L Speed Limit'),
                    icon: '/pixmaps/downloading16.png',
                    items: [
                        {
                            type: 'text',
                            action: 'max_download_speed',
                            value: 5,
                            text: '5 KiB/s'
                        },
                        {
                            type: 'text',
                            action: 'max_download_speed',
                            value: 10,
                            text: '10 KiB/s'
                        },
                        {
                            type: 'text',
                            action: 'max_download_speed',
                            value: 30,
                            text: '30 KiB/s'
                        },
                        {
                            type: 'text',
                            action: 'max_download_speed',
                            value: 80,
                            text: '80 KiB/s'
                        },
                        {
                            type: 'text',
                            action: 'max_download_speed',
                            value: 300,
                            text: '300 KiB/s'
                        },
                        {
                            type: 'text',
                            action: 'max_download_speed',
                            value: -1,
                            text: _('Unlimited')
                        }
                    ]
                },
                {
                    type: 'submenu',
                    text: _('U/L Speed Limit'),
                    icon: '/pixmaps/seeding16.png',
                    items: [
                        {
                            type: 'text',
                            action: 'max_upload_speed',
                            value: 5,
                            text:'5 KiB/s'
                        },
                        {
                            type: 'text',
                            action: 'max_upload_speed',
                            value: 10,
                            text: '10 KiB/s'
                        },
                        {
                            type: 'text',
                            action: 'max_upload_speed',
                            value: 30,
                            text: '30 KiB/s'
                        },
                        {
                            type: 'text',
                            action: 'max_upload_speed',
                            value: 80,
                            text: '80 KiB/s'
                        },
                        {
                            type: 'text',
                            action: 'max_upload_speed',
                            value: 300,
                            text: '300 KiB/s'
                        },
                        {
                            type: 'text',
                            action: 'max_upload_speed',
                            value: -1,
                            text: _('Unlimited')
                        }
                    ]
                },
                {
                    type: 'submenu',
                    text: _('Connection Limit'),
                    icon: '/static/images/16/connections.png',
                    items: [
                        {
                            type: 'text',
                            action: 'max_connections',
                            value: 50,
                            text: '50'
                        },
                        {
                            type: 'text',
                            action: 'max_connections',
                            value: 100,
                            text: '100'
                        },
                        {
                            type: 'text',
                            action: 'max_connections',
                            value: 200,
                            text: '200'
                        },
                        {
                            type: 'text',
                            action: 'max_connections',
                            value: 300,
                            text: '300'
                        },
                        {
                            type: 'text',
                            action: 'max_connections',
                            value: 500,
                            text: '500'
                        },
                        {
                            type: 'text',
                            action: 'max_connections',
                            value: -1,
                            text: _('Unlimited')
                        }
                    ]
                },
                {
                    type: 'submenu',
                    text: _('Upload Slot Limit'),
                    icon: '/template/static/icons/16/view-sort-ascending.png',
                    items: [
                        {
                            type: 'text',
                            action: 'max_upload_slots',
                            value: 0,
                            text: '0'
                        },
                        {
                            type: 'text',
                            action: 'max_upload_slots',
                            value: 1,
                            text: '1'
                        },
                        {
                            type: 'text',
                            action: 'max_upload_slots',
                            value: 2,
                            text: '2'
                        },
                        {
                            type: 'text',
                            action: 'max_upload_slots',
                            value: 3,
                            text: '3'
                        },
                        {
                            type: 'text',
                            action: 'max_upload_slots',
                            value: 5,
                            text: '5'
                        },
                        {
                            type: 'text',
                            action: 'max_upload_slots',
                            value: -1,
                            text: _('Unlimited')}
                    ]
                },
                {
                    type: 'toggle',
                    action: 'auto_managed',
                    value: false,
                    text: _('Auto Managed')
                }
            ]
        },
        {type:'seperator'},
        {
            type: 'submenu',
            text: _('Queue'),
            icon: '/template/static/icons/16/view-sort-descending.png',
            items: [
                {
                    type: 'text',
                    action: 'top',
                    text: _('Top'),
                    icon: '/static/images/16/go-top.png'
                },
                {
                    type: 'text',
                    action: 'up',
                    text: _('Up'),
                    icon: '/static/images/16/queue-up.png'
                },
                {
                    type: 'text',
                    action: 'down',
                    text: _('Down'),
                    icon: '/static/images/16/queue-down.png'
                },
                {
                    type: 'text',
                    action: 'bottom',
                    text: _('Bottom'),
                    icon: '/static/images/16/go-bottom.png'
                }
            ]
        },
        {type: 'seperator'},
        {
            type: 'text',
            action: 'update_tracker',
            text: _('Update Tracker'),
            icon: '/template/static/icons/16/view-refresh.png'
        },
        {
            type: 'text',
            action: 'edit_trackers',
            text: _('Edit Trackers'),
            icon: '/template/static/icons/16/gtk-edit.png'
        },
        {type:'seperator'},
        {
            type: 'submenu',
            action: 'remove',
            value: 0,
            text: _('Remove Torrent'),
            icon: '/static/images/16/list-remove.png',
            items: [
                {
                    type: 'text',
                    action: 'remove',
                    value: 0,
                    text: _('From Session')
                },
                {
                    type: 'text',
                    action: 'remove',
                    value: 1,
                    text: _('... and delete Torrent file')
                },
                {
                    type: 'text',
                    action: 'remove',
                    value: 2,
                    text: _('... and delete Downloaded files')
                },
                {
                    type: 'text',
                    action: 'remove',
                    value: 3,
                    text: _('... and delete All files')
                }
            ]
        },
        {type:'seperator'},
        {
            type: 'text',
            action: 'force_recheck',
            text: _('Force Recheck'),
            icon: '/static/images/16/edit-redo.png'
        },
        {
            type: 'text',
            action: 'move_storage',
            text: _('Move Storage'),
            icon: '/static/images/16/move.png'
        }
    ],

    Connections: [
        {
            type: 'text',
            action: 'max_connections',
            value: 50,
            text: '50'
        },
        {
            type: 'text',
            action: 'max_connections',
            value: 100,
            text: '100'
        },
        {
            type: 'text',
            action: 'max_connections',
            value: 200,
            text: '200'
        },
        {
            type: 'text',
            action: 'max_connections',
            value: 300,
            text: '300'
        },
        {
            type: 'text',
            action: 'max_connections',
            value: 500,
            text: '500'
        },
        {
            type: 'text',
            action: 'max_connections',
            value: -1,
            text: _('Unlimited')
        }
    ],

    Download: [
        {
            type: 'text',
            action: 'max_download_speed',
            value: 5,
            text: '5 KiB/s'
        },
        {
            type: 'text',
            action: 'max_download_speed',
            value: 10,
            text: '10 KiB/s'
        },
        {
            type: 'text',
            action: 'max_download_speed',
            value: 30,
            text: '30 KiB/s'
        },
        {
            type: 'text',
            action: 'max_download_speed',
            value: 80,
            text: '80 KiB/s'
        },
        {
            type: 'text',
            action: 'max_download_speed',
            value: 300,
            text: '300 KiB/s'
        },
        {
            type: 'text',
            action: 'max_download_speed',
            value: -1,
            text: _('Unlimited')
        }
    ],

    Upload: [
        {
            type: 'text',
            action: 'max_upload_speed',
            value: 5,
            text:'5 KiB/s'
        },
        {
            type: 'text',
            action: 'max_upload_speed',
            value: 10,
            text: '10 KiB/s'
        },
        {
            type: 'text',
            action: 'max_upload_speed',
            value: 30,
            text: '30 KiB/s'
        },
        {
            type: 'text',
            action: 'max_upload_speed',
            value: 80,
            text: '80 KiB/s'
        },
        {
            type: 'text',
            action: 'max_upload_speed',
            value: 300,
            text: '300 KiB/s'
        },
        {
            type: 'text',
            action: 'max_upload_speed',
            value: -1,
            text: _('Unlimited')
        }
    ]
};
