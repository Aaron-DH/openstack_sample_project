import gettext
import os

import oslo_i18n

DOMAIN = 'report'


_translators = oslo_i18n.TranslatorFactory(domain=DOMAIN)

# The primary translation function using the well-known name "_"
_ = _translators.primary

# Translators for log levels.
#
# The abbreviated names are meant to reflect the usual use of a short
# name like '_'. The "L" is for "log" and the other letter comes from
# the level.
_LI = _translators.log_info
_LW = _translators.log_warning
_LE = _translators.log_error
_LC = _translators.log_critical


def translate(value, user_locale):
    return oslo_i18n.translate(value, user_locale)


def get_available_languages():
    return oslo_i18n.get_available_languages(DOMAIN)


# For report_file Translate
path = os.path.split(__file__)[0] + '/locale'

_F = _

try:
    t = gettext.translation('lang', path, languages=['zh_CN'])
    _F = t.ugettext
except Exception:
    pass
