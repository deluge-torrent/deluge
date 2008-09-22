/*
 * Script: deluge-menus.js
 *  Contains the layout for all the popup menus used within the ajax ui.
 *
 * Copyright:
 *   Damien Churchill (c) 2008
 */

Deluge.Menus = {
    Torrents: [
        {
            type:'text',
            action:'pause',
            text: Deluge.Strings.get('Pause'),
            icon:'/static/images/tango/pause.png'
        },
        {
            type: 'text',
            action: 'resume',
            text: Deluge.Strings.get('Resume'),
            icon: '/static/images/tango/start.png'
        },
        { type: 'seperator' },
        {
            type:'submenu',
            text: Deluge.Strings.get('Options'),
            icon:'/static/images/tango/preferences-system.png',
            items: [
                {
                    type: 'submenu',
                    text: Deluge.Strings.get('D/L Speed Limit'),
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
                            text: Deluge.Strings.get('Unlimited')
                        }
                    ]
                },
                {
                    type: 'submenu',
                    text: Deluge.Strings.get('U/L Speed Limit'),
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
                            text: Deluge.Strings.get('Unlimited')
                        }
                    ]
                },
                {
                    type: 'submenu',
                    text: Deluge.Strings.get('Connection Limit'),
                    icon: '/static/images/tango/connections.png',
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
                            text: Deluge.Strings.get('Unlimited')
                        }
                    ]
                },
                {
                    type: 'submenu',
                    text: Deluge.Strings.get('Upload Slot Limit'),
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
                            text: Deluge.Strings.get('Unlimited')}
                    ]
                },
                {
                    type: 'toggle',
                    action: 'auto_managed',
                    value: false,
                    text: Deluge.Strings.get('Auto Managed')
                }
            ]
        },
        {type:'seperator'},
        {
            type: 'submenu',
            text: Deluge.Strings.get('Queue'),
            icon: '/template/static/icons/16/view-sort-descending.png',
            items: [
                {
                    type: 'text',
                    action: 'top',
                    text: Deluge.Strings.get('Top'),
                    icon: '/static/images/tango/go-top.png'
                },
                {
                    type: 'text',
                    action: 'up',
                    text: Deluge.Strings.get('Up'),
                    icon: '/static/images/tango/queue-up.png'
                },
                {
                    type: 'text',
                    action: 'down',
                    text: Deluge.Strings.get('Down'),
                    icon: '/static/images/tango/queue-down.png'
                },
                {
                    type: 'text',
                    action: 'bottom',
                    text: Deluge.Strings.get('Bottom'),
                    icon: '/static/images/tango/go-bottom.png'
                }
            ]
        },
        {type: 'seperator'}, 
        {
            type: 'text',
            action: 'update_tracker',
            text: Deluge.Strings.get('Update Tracker'),
            icon: '/template/static/icons/16/view-refresh.png'
        },
        {
            type: 'text',
            action: 'edit_trackers',
            text: Deluge.Strings.get('Edit Trackers'),
            icon: '/template/static/icons/16/gtk-edit.png'
        },
        {type:'seperator'},
        {
            type: 'submenu',
            action: 'remove',
            value: 0,
            text: Deluge.Strings.get('Remove Torrent'),
            icon: '/static/images/tango/list-remove.png',
            items: [
                {
                    type: 'text',
                    action: 'remove',
                    value: 0,
                    text: Deluge.Strings.get('From Session')
                },
                {
                    type: 'text',
                    action: 'remove',
                    value: 1,
                    text: Deluge.Strings.get('... and delete Torrent file')
                },
                {
                    type: 'text',
                    action: 'remove',
                    value: 2,
                    text: Deluge.Strings.get('... and delete Downloaded files')
                },
                {
                    type: 'text',
                    action: 'remove',
                    value: 3,
                    text: Deluge.Strings.get('... and delete All files')
                }
            ]
        },
        {type:'seperator'},
        {
            type: 'text',
            action: 'force_recheck',
            text: Deluge.Strings.get('Force Recheck'),
            icon: '/static/images/tango/edit-redo.png'
        },
        {
            type: 'text',
            action: 'move_storage',
            text: Deluge.Strings.get('Move Storage'),
            icon: '/static/images/tango/move.png'
        }
    ]
}
