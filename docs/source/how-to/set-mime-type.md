# How to set Deluge as default torrent application

## Check registered mime types

gio mime application/x-bittorrent
gio mime x-scheme-handler/magnet

## Set Deluge as default mime

gio mime x-scheme-handler/magnet deluge.desktop
gio mime application/x-bittorrent deluge.desktop

## Troubleshooting

update-mime-database ~/.local/share/mime
update-desktop-database ~/.local/share/applications

### XDG Check

xdg-mime query default x-scheme-handler/magnet

## References

https://help.gnome.org/admin/system-admin-guide/stable/mime-types-custom-user.html.en
