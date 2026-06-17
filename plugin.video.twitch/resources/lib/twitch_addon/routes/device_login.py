# -*- coding: utf-8 -*-
"""

    Interactive Twitch OAuth Device Code login.

    Shows a user code + verification URL, polls until the user authorises on
    twitch.tv/activate, then stores access + refresh token. From then on the
    token is renewed automatically (see addon.utils.ensure_valid_token) -- no
    more manual token regeneration.

    SPDX-License-Identifier: GPL-3.0-only
"""

import time

import xbmcgui

from ..addon import utils, device_oauth
from ..addon.common import kodi, log_utils
from ..addon.constants import SCOPES
from ..addon.utils import i18n


def route():
    heading = i18n('login_device_code')
    client_id = utils.get_client_id()
    scopes = ' '.join(SCOPES)

    ok, data = device_oauth.request_device_code(client_id, scopes)
    if not ok or not data.get('user_code'):
        msg = data.get('message') or data.get('error') or ''
        kodi.Dialog().ok(heading, i18n('device_login_failed_clientid') % msg)
        return

    user_code = data['user_code']
    device_code = data['device_code']
    interval = int(data.get('interval', 5)) or 5
    expires_in = int(data.get('expires_in', 1800)) or 1800

    # Kurze, saubere Aktivierungs-URL (Twitchs verification_uri enthält den Code als langen Query-Anhang).
    activate_url = 'https://www.twitch.tv/activate'
    body = i18n('device_login_body') % (activate_url, user_code)
    progress = xbmcgui.DialogProgress()
    progress.create(heading, body)

    token = None
    waited = 0
    while waited < expires_in:
        # wait the poll interval, abortable
        slept = 0
        while slept < interval:
            if progress.iscanceled():
                progress.close()
                kodi.notify(kodi.get_name(), i18n('login_cancelled'), sound=False)
                return
            time.sleep(1)
            slept += 1
            waited += 1
        status, tdata = device_oauth.poll_device_token(client_id, scopes, device_code)
        if status == 'ok':
            token = tdata
            break
        elif status == 'slow_down':
            interval += 2
        elif status in ('expired', 'denied'):
            progress.close()
            kodi.notify(kodi.get_name(),
                        i18n('login_expired') if status == 'expired' else i18n('login_denied'),
                        sound=False)
            return
        # 'pending' / transient 'error' -> keep polling
        pct = int(min(99, (waited * 100) // expires_in))
        try:
            progress.update(pct, body + '[CR]' + i18n('waiting_confirmation'))
        except Exception:
            pass

    progress.close()
    if token and token.get('access_token'):
        utils.store_oauth_tokens(token['access_token'],
                                 token.get('refresh_token', ''),
                                 token.get('expires_in', 14400))
        log_utils.log('OAuth: device login succeeded, refresh token stored', log_utils.LOGNOTICE)
        kodi.Dialog().ok(heading, i18n('login_success'))
    else:
        kodi.notify(kodi.get_name(), i18n('login_failed'), sound=False)
