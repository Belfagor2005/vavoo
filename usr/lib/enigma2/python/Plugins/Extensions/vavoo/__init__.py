# -*- coding: utf-8 -*-

from __future__ import absolute_import
__author__ = "Lululla"
__email__ = "ekekaz@gmail.com"
__copyright__ = 'Copyright (c) 2024 Lululla'
__license__ = "CC BY-NC-SA 4.0"
__version__ = "1.42"

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext
import os


PluginLanguageDomain = 'vavoo'
PluginLanguagePath = 'Extensions/vavoo/locale'


def paypal():
    conthelp = "If you like what I do you\n"
    conthelp += "can contribute with a coffee\n"
    conthelp += "scan the qr code and donate € 1.00"
    return conthelp


isDreamOS = False
if os.path.exists("/usr/bin/apt-get"):
    isDreamOS = True


def localeInit():
    if isDreamOS:
        lang = language.getLanguage()[:2]
        os.environ["LANGUAGE"] = lang
    gettext.bindtextdomain(
        PluginLanguageDomain,
        resolveFilename(
            SCOPE_PLUGINS,
            PluginLanguagePath))


if isDreamOS:
    def _(txt):
        return gettext.dgettext(PluginLanguageDomain, txt) if txt else ""
else:
    def _(txt):
        translated = gettext.dgettext(PluginLanguageDomain, txt)
        if translated:
            return translated
        else:
            print(("[%s] fallback to default translation for %s" %
                  (PluginLanguageDomain, txt)))
            return gettext.gettext(txt)

localeInit()
language.addCallback(localeInit)


country_codes = {
    "Albania": "al",
    "Arabia": "sa",
    "Balkans": "bk",
    "Bulgaria": "bg",
    "Croatia": "hr",
    "France": "fr",
    "Germany": "de",
    "Italy": "it",
    "Netherlands": "nl",
    "Poland": "pl",
    "Portugal": "pt",
    "Romania": "ro",
    "Russia": "ru",
    "Spain": "es",
    "Turkey": "tr",
    "United Kingdom": "gb"
}
