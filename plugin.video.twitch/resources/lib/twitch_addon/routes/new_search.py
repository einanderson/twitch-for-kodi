# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon.common import kodi
from ..addon.utils import i18n


def route(api, content):
    # Render results inline instead of redirecting via Container.Update: the redirect
    # is swallowed under reuselanguageinvoker=true (empty list, esp. on SZ). Pagination
    # ("next page") still uses MODES.SEARCHRESULTS directly in search_results.py.
    user_input = kodi.get_keyboard(i18n('search'))
    if not user_input:
        return
    from . import search_results
    search_results.route(api, content, user_input)
