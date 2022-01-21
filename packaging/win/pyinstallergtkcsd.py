import os

ENV_GTK_CSD = os.getenv('GTK_CSD')


def setup_gtk_csd():
    if ENV_GTK_CSD is not None:
        return
    else:
        os.environ['GTK_CSD'] = '0'


setup_gtk_csd()
