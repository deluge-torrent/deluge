try:
    _('translate something')
except:
    import gettext
    gettext.install('locale')

ugettext = _
ugettext_lazy = _

