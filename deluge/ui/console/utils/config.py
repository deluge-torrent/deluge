def migrate_1_to_2(config):
    """Create better structure by moving most settings out of dict root
    and into sub categories. Some keys are also renamed to be consistent
    with other UIs.
    """

    def move_key(source, dest, source_key, dest_key=None):
        if dest_key is None:
            dest_key = source_key

        dest[dest_key] = source[source_key]
        del source[source_key]

    # These are moved to 'torrentview' sub dict
    for k in [
        'sort_primary',
        'sort_secondary',
        'move_selection',
        'separate_complete',
    ]:
        move_key(config, config['torrentview'], k)

    # These are moved to 'addtorrents' sub dict
    for k in [
        'show_misc_files',
        'show_hidden_folders',
        'sort_column',
        'reverse_sort',
        'last_path',
    ]:
        move_key(config, config['addtorrents'], 'addtorrents_%s' % k, dest_key=k)

    # These are moved to 'cmdline' sub dict
    for k in [
        'ignore_duplicate_lines',
        'torrents_per_tab_press',
        'third_tab_lists_all',
    ]:
        move_key(config, config['cmdline'], k)

    move_key(
        config,
        config['cmdline'],
        'save_legacy_history',
        dest_key='save_command_history',
    )

    # Add key for localization
    config['language'] = ''

    # Migrate column settings
    columns = [
        'queue',
        'size',
        'state',
        'progress',
        'seeds',
        'peers',
        'downspeed',
        'upspeed',
        'eta',
        'ratio',
        'avail',
        'added',
        'tracker',
        'savepath',
        'downloaded',
        'uploaded',
        'remaining',
        'owner',
        'downloading_time',
        'seeding_time',
        'completed',
        'seeds_peers_ratio',
        'complete_seen',
        'down_limit',
        'up_limit',
        'shared',
        'name',
    ]
    column_name_mapping = {
        'downspeed': 'download_speed',
        'upspeed': 'upload_speed',
        'added': 'time_added',
        'savepath': 'download_location',
        'completed': 'completed_time',
        'complete_seen': 'last_seen_complete',
        'down_limit': 'max_download_speed',
        'up_limit': 'max_upload_speed',
        'downloading_time': 'active_time',
    }

    from deluge.ui.console.modes.torrentlist.torrentview import default_columns

    # These are moved to 'torrentview.columns' sub dict
    for k in columns:
        column_name = column_name_mapping.get(k, k)
        config['torrentview']['columns'][column_name] = {}
        if k == 'name':
            config['torrentview']['columns'][column_name]['visible'] = True
        else:
            move_key(
                config,
                config['torrentview']['columns'][column_name],
                'show_%s' % k,
                dest_key='visible',
            )
        move_key(
            config,
            config['torrentview']['columns'][column_name],
            '%s_width' % k,
            dest_key='width',
        )
        config['torrentview']['columns'][column_name]['order'] = default_columns[
            column_name
        ]['order']

    return config
