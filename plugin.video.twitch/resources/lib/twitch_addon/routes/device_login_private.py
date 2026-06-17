# -*- coding: utf-8 -*-
"""

    Interactive device-code login for the PRIVATE (kimne78/Turbo) credentials.

    Same flow as device_login, but uses the private client id (kimne78) and stores the
    result in the private token store (auto-refreshed). This is what usher/GQL uses for
    ad-free Turbo/subscriber playback. Additive to the manual `private_oauth_token` field.

    SPDX-License-Identifier: GPL-3.0-only
"""

import time

import xbmcgui

from ..addon import utils, device_oauth
from ..addon.common import kodi, log_utils
from ..addon.utils import i18n

KIMNE_CLIENT_ID = 'kimne78kx3ncx6brgo4mv6wki5h1ko'


def route():
    heading = i18n('login_private_heading')
    client_id = utils.get_private_client_id() or KIMNE_CLIENT_ID
    scopes = ''  # kimne78 playback entitlement (Turbo/sub) needs no scopes

    ok, data = device_oauth.request_device_code(client_id, scopes)
    if not ok or not data.get('user_code'):
        msg = data.get('message') or data.get('error') or ''
        kodi.Dialog().ok(heading, i18n('device_login_failed_clientid') % msg)
        return

    user_code = data['user_code']
    device_code = data['device_code']
    interval = int(data.get('interval', 5)) or 5
    expires_in = int(data.get('expires_in', 1800)) or 1800

    activate_url = 'https://www.twitch.tv/activate'
    body = i18n('device_login_private_body') % (activate_url, user_code)
    progress = xbmcgui.DialogProgress()
    progress.create(heading, body)

    token = None
    waited = 0
    while waited < expires_in:
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
        pct = int(min(99, (waited * 100) // expires_in))
        try:
            progress.update(pct, body + '[CR]' + i18n('waiting_confirmation'))
        except Exception:
            pass

    progress.close()
    if token and token.get('access_token'):
        utils.store_private_tokens(token['access_token'],
                                   token.get('refresh_token', ''),
                                   token.get('expires_in', 14400))
        log_utils.log('OAuth(private): device login succeeded, refresh token stored', log_utils.LOGNOTICE)
        kodi.Dialog().ok(heading, i18n('login_private_success'))
    else:
        kodi.notify(kodi.get_name(), i18n('login_failed'), sound=False)
