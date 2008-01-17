#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# deluge_webserver.py
#
# Copyright (C) Martijn Voncken 2008 <mvoncken@gmail.com>
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
# along with this program.  If not, write to:
#     The Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor
#     Boston, MA  02110-1301, USA.
#
#  In addition, as a special exception, the copyright holders give
#  permission to link the code of portions of this program with the OpenSSL
#  library.
#  You must obey the GNU General Public License in all respects for all of
#  the code used other than OpenSSL. If you modify file(s) with this
#  exception, you may extend this exception to your version of the file(s),
#  but you are not obligated to do so. If you do not wish to do so, delete
#  this exception statement from your version. If you delete this exception
#  statement from all source files in the program, then also delete it here.

import lib.newforms as forms
import page_decorators as deco
import lib.webpy022 as web
from webserver_common import ws
from render import render
from lib.webpy022.http import seeother
import sys
import os

groups = []
blocks = forms.utils.datastructures.SortedDict()

class Form(forms.Form):
    info = ""
    title = "No Title"
    def __init__(self,data = None):
        if data == None:
            data = self.initial_data()
        forms.Form.__init__(self,data)

    def initial_data(self):
        "override in subclass"
        return None

    def start_save(self):
        "called by config_page"
        data = web.Storage(self.clean_data)
        self.validate(data)
        self.save(data)
        self.post_save()

    def save(self, vars):
        "override in subclass"
        raise NotImplementedError()

    def post_save(self):
        pass

    def validate(self, data):
        pass


class WebCfgForm(Form):
    "config base for webui"
    def initial_data(self):
        return ws.config

    def save(self, data):
        ws.config.update(data)
        ws.save_config()

class CookieCfgForm(Form):
    "config base for webui"
    def initial_data(self):
        return ws.config

    def save(self, data):
        ws.config.update(data)
        ws.save_config()


class CfgForm(Form):
    "config base for deluge-cfg"
    def initial_data(self):
        return ws.proxy.get_config()
    def save(self, data):
        ws.proxy.set_config(dict(data))


#convenience Input Fields.
class _IntInput(forms.TextInput):
    """
    because deluge-floats are edited as ints.
    """
    def render(self, name, value, attrs=None):
        try:
            value = int(float(value))
            if value == -1:
                value = _("Unlimited")
        except:
            pass
        return forms.TextInput.render(self, name, value, attrs)

class CheckBox(forms.BooleanField):
    "Non Required ChoiceField"
    def __init__(self,label, **kwargs):
        forms.BooleanField.__init__(self,label=label,required=False,**kwargs)

class IntCombo(forms.ChoiceField):
    """
    choices are the display-values
    returns int for the chosen display-value.
    """
    def __init__(self, label, choices, **kwargs):
        forms.ChoiceField.__init__(self, label=label,
            choices=enumerate(choices), **kwargs)

    def clean(self, value):
        return int(forms.ChoiceField.clean(self, value))

class DelugeInt(forms.IntegerField):
    def __init__(self, label , **kwargs):
        forms.IntegerField.__init__(self, label=label, min_value=-1,
            max_value=sys.maxint, widget=_IntInput, **kwargs)

    def clean(self, value):
        if str(value).lower() == _('Unlimited').lower():
            value = -1
        return int(forms.IntegerField.clean(self, value))

class DelugeFloat(DelugeInt):
    def clean(self, value):
        return int(DelugeInt.clean(self, value))

class MultipleChoice(forms.MultipleChoiceField):
    #temp/test
    def __init__(self, label, choices, **kwargs):
        forms.MultipleChoiceField.__init__(self, label=label, choices=choices,
            widget=forms.CheckboxSelectMultiple, required=False)

class ServerFolder(forms.CharField):
    def __init__(self, label, **kwargs):
        forms.CharField.__init__(self, label=label,**kwargs)

    def clean(self, value):
        value = value.rstrip('/').rstrip('\\')
        self.validate(value)
        return forms.CharField.clean(self, value)

    def validate(self, value):
        if (value and not os.path.isdir(value)):
            raise forms.ValidationError(_("This folder does not exist."))

class Password(forms.CharField):
    def __init__(self, label, **kwargs):
        forms.CharField.__init__(self, label=label, widget=forms.PasswordInput,
            **kwargs)

#/fields

class config_page:
    """
    web.py config page
    """
    def get_form_class(self,name):
        try:
            return blocks[name]
        except KeyError:
            raise Exception('no config page named:"%s"')

    @deco.deluge_page
    def GET(self, name):
        if name == '':
            return seeother('/config/template')

        form_class = self.get_form_class(name)
        f = form_class()
        f.full_clean()
        return self.render(f , name)

    @deco.deluge_page
    def POST(self,name):

        form_class = self.get_form_class(name)
        fields = form_class.base_fields.keys()
        form_data = web.Storage()
        vars = web.input()
        for field in fields:
            form_data[field] = vars.get(field)
            #DIRTY HACK: (for multiple-select)
            if isinstance(form_class.base_fields[field],
                    forms.MultipleChoiceField):
                form_data[field] = web.input(**{field:[]})[field]
            #/DIRTY HACK

        form = form_class(form_data)
        if form.is_valid():
            ws.log.debug('save config %s' % form_data)
            try:
                form.start_save()
                return self.render(form , name, _('These changes were saved'))
            except forms.ValidationError, e:
                ws.log.debug(e.message)
                return self.render(form , name, error = e.message)
        else:
            return self.render(form , name,
                error= _('Correct the errors above and try again'))

    def render(self, f , name , message = '' , error=''):
        return render.config(groups, blocks, f, name , message , error)

def register_block(group, name, form):
    if not group in groups:
        groups.append(group)
    form.group = group
    blocks[name] = form

def unregister_block(name):
    del blocks[name]





