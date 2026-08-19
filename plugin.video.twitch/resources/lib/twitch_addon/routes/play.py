# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils
from ..addon.common import kodi, log_utils
from ..addon.constants import Keys, LINE_LENGTH
from ..addon.converter import JsonListItemConverter
from ..addon.twitch_exceptions import PlaybackFailed, SubRequired, TwitchException


def _best_clip(videos):
    # clip qualities are plain MP4s; 'source' is the original quality
    for video in videos:
        if 'source' in video.get('id', '').lower():
            return video
    return videos[0] if videos else None


def route(api, seek_time=0, channel_id=None, video_id=None, slug=None, ask=False, use_player=False, quality=None, channel_name=None):
    # ask/quality are accepted for URL compatibility (old favourites/shortcuts) but
    # ignored: live streams and VODs always play adaptively via InputStream Adaptive.
    converter = JsonListItemConverter(LINE_LENGTH)
    window = kodi.Window(10000)

    def _reset():
        window.clearProperty(kodi.get_id() + '-_seek')
        window.clearProperty(kodi.get_id() + '-seek_time')
        window.clearProperty(kodi.get_id() + '-twitch_playing')

    def _reset_live():
        window.clearProperty(kodi.get_id() + '-livestream')

    def _get_seek():
        _result = window.getProperty(kodi.get_id() + '-_seek')
        if _result:
            return _result.split(',')
        return None, None

    def _set_playing():
        window.setProperty(kodi.get_id() + '-twitch_playing', str(True))

    def _set_live(_id, _name, _display_name):
        window.setProperty(kodi.get_id() + '-livestream', '%s,%s,%s,%s' % (_id, _name, _display_name, 'Adaptive'))

    def _set_seek_time(value):
        window.setProperty(kodi.get_id() + '-seek_time', str(value))

    def _resolve(playback_item, play_url):
        _set_playing()
        if use_player:
            kodi.Player().play(play_url, playback_item)
        else:
            kodi.set_resolved_url(playback_item)

    try:
        _reset_live()
        seek_time = int(seek_time)

        if video_id:
            seek_id, _seek_time = _get_seek()
            if seek_id == video_id:
                seek_time = int(_seek_time)

            result = api.get_video_by_id(video_id)
            result = result.get(Keys.DATA, [{}])[0]
            video_id = result[Keys.ID]
            channel_id = result[Keys.USER_ID]
            channel_name = result[Keys.USER_NAME] if result[Keys.USER_NAME] else result[Keys.USER_LOGIN]

            # subscriber-only VODs: bail out early with a clear message
            try:
                extra_info = api._get_video_token(video_id)  # NOQA
            except TwitchException:
                extra_info = dict()
            if api.access_token:
                try:
                    subscribed = api.check_subscribed(channel_id)
                except TwitchException as e:
                    if ('status' in e.message) and (e.message['status'] == 422):
                        subscribed = True  # no subscription program
                    else:
                        raise
            else:
                subscribed = False
            if not subscribed:
                unrestricted = result.get(Keys.RESOLUTIONS, dict())
                if unrestricted:
                    unrestricted[u'audio_only'] = u''
                if ('chansub' in extra_info) and ('restricted_bitrates' in extra_info['chansub']):
                    log_utils.log('Restricted qualities |%s|' % extra_info['chansub']['restricted_bitrates'], log_utils.LOGDEBUG)
                    for res in extra_info['chansub']['restricted_bitrates']:
                        if res in unrestricted:
                            del unrestricted[res]
                    if unrestricted == {}:
                        raise SubRequired(channel_name)

            _reset()
            if not utils.use_inputstream_adaptive():
                raise PlaybackFailed()
            request = api.video_request(video_id)
            if not request:
                raise PlaybackFailed()

            item_dict = converter.video_to_playitem(result)
            playback_item = kodi.create_item(item_dict, add=False)
            playback_item.addStreamInfo('video', {})
            playback_item.addStreamInfo('audio', {'channels': '2'})
            playback_item.setContentLookup(False)
            playback_item.setMimeType('application/x-mpegURL')
            play_url = utils.prepare_adaptive_playback(playback_item, request)
            log_utils.log('Attempting playback using |%s|' % play_url, log_utils.LOGDEBUG)
            if seek_time > 0:
                _set_seek_time(seek_time)
            _resolve(playback_item, play_url)
            return

        elif channel_id or channel_name:
            if channel_name and not channel_id:
                result = api.get_user_ids(channel_name)
                if result:
                    channel_id = result[0]
            if channel_id:
                id_only = False
                name = None
                result = api.get_channel_stream(channel_id)[Keys.DATA]
                if result:
                    result = result[0]
                    channel_name = result[Keys.USER_NAME] \
                        if result[Keys.USER_NAME] else result[Keys.USER_LOGIN]
                    name = result[Keys.USER_LOGIN]
                else:  # rerun
                    user = api.get_users(user_ids=channel_id)
                    if user.get(Keys.DATA, [{}]):
                        user = user[Keys.DATA][0]
                        id_only = True
                        name = user.get(Keys.LOGIN)
                        result = {
                            Keys.USER_NAME: user.get(Keys.DISPLAY_NAME, Keys.LOGIN),
                            Keys.USER_LOGIN: user.get(Keys.LOGIN),
                            Keys.USER_ID: user.get(Keys.ID),
                        }  # make a dummy result to continue with playback
                if name:
                    _reset()
                    if not utils.use_inputstream_adaptive():
                        raise PlaybackFailed()
                    request = api.live_request(name)
                    if not request:
                        raise PlaybackFailed()

                    _set_live(channel_id, name, channel_name)
                    item_dict = converter.stream_to_playitem(result, id_only=id_only)
                    playback_item = kodi.create_item(item_dict, add=False)
                    playback_item.addStreamInfo('video', {})
                    playback_item.addStreamInfo('audio', {'channels': '2'})
                    playback_item.setContentLookup(False)
                    playback_item.setMimeType('application/x-mpegURL')
                    play_url = utils.prepare_adaptive_playback(playback_item, request)
                    log_utils.log('Attempting playback using |%s|' % play_url, log_utils.LOGDEBUG)
                    _resolve(playback_item, play_url)
                    return

        elif slug:
            result = api.get_clip_by_slug(slug)
            result = result.get(Keys.DATA, [{}])[0]
            videos = api.get_clip(slug)
            video = _best_clip(videos)
            _reset()
            if video:
                item_dict = converter.clip_to_playitem(result)
                item_dict['path'] = video['url'] + '|verifypeer=false'
                playback_item = kodi.create_item(item_dict, add=False)
                playback_item.addStreamInfo('video', {})
                playback_item.addStreamInfo('audio', {'channels': '2'})
                if video['url'].endswith('mp4'):
                    playback_item.setContentLookup(False)
                    playback_item.setMimeType('video/mp4')
                log_utils.log('Attempting clip playback using quality |%s| @ |%s|' % (video['name'], video['url']), log_utils.LOGDEBUG)
                _resolve(playback_item, item_dict['path'])
                return

        raise PlaybackFailed()
    except:
        _reset()
        _reset_live()
        raise
