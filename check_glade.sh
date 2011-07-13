#!/bin/sh

# Fixes glade files which may have set gtk stock labels set to translatable
for x in `find . -name '*.glade' |grep -v '.git\|build'` ; do \
    for y in gtk-add gtk-apply gtk-bold gtk-cancel gtk-cdrom gtk-clear \
        gtk-close gtk-color-picker gtk-connect gtk-convert gtk-copy gtk-cut \
        gtk-delete gtk-dialog-error gtk-dialog-info gtk-dialog-question \
        gtk-dialog-warning gtk-dnd gtk-dnd-multiple gtk-edit gtk-execute gtk-find \
        gtk-find-and-replace gtk-floppy gtk-goto-bottom gtk-goto-first \
        gtk-goto-last gtk-goto-top gtk-go-back gtk-go-down gtk-go-forward \
        gtk-go-up gtk-help gtk-home gtk-index gtk-italic gtk-jump-to \
        gtk-justify-center gtk-justify-fill gtk-justify-left gtk-missing-image \
        gtk-new gtk-no gtk-ok gtk-open gtk-paste gtk-preferences gtk-print \
        gtk-print-preview gtk-properties gtk-quit gtk-redo gtk-refresh \
        gtk-remove gtk-revert-to-saved gtk-save gtk-save-as gtk-select-color \
        gtk-select-font gtk-sort-descending gtk-spell-check gtk-stop \
        gtk-strikethrough gtk-undelete gtk-underline gtk-undo gtk-yes \
        gtk-zoom-100 gtk-zoom-fit gtk-zoom-in gtk-zoom-out; do \
            sed -i "s/<property\ name\=\"label\"\ translatable\=\"yes\">$y<\/property>/<property\ name\=\"label\"\ translatable\=\"no\">$y<\/property>/g" $x; \
        done;\
    done
