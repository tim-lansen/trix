'use strict'

#$ = require('jquery')
#LiveCrop = require('./pages/ui/live_crop')
#InteractionPlayer = require('./pages/ui/interaction_player')
#InteractionInternal = require('./models/InteractionInternal')
Rightholders = require('./models/Rightholders')
AudioContext = window.AudioContext or window.webkitAudioContext


absY = (obj) ->
    top = 0
    while typeof obj.offsetTop == 'number'
        top += obj.offsetTop
        obj = obj.parentNode
    top

absX = (obj) ->
    left = 0
    while typeof obj.offsetLeft == 'number'
        left += obj.offsetLeft
        obj = obj.parentNode
    left

padz = (number, size) ->
    pad = size - (('' + number).length)
    z = ''
    while pad > 0
        z += '0'
        pad -= 1
    z + number

g_InteractionPlayer = null

class AudioMan
    @single_channel_re: /1\schannels\s\((.+)\)/
    @audioLayouts: [
        {'code': 'mono',           'name': 'Mono',            'layout': ['FC']}
        {'code': 'stereo',         'name': 'Stereo',          'layout': ['FL',  'FR']}
        {'code': '2.1',            'name': '2.1',             'layout': ['FL',  'FR',  'LFE']}
        {'code': '3.0',            'name': '3.0',             'layout': ['FL',  'FR',  'FC']}
        #{'code': '3.0(back)',      'name': '3.0 (back)',      'layout': ['FL',  'FR',  'BC']}
        {'code': '4.0',            'name': '4.0',             'layout': ['FL',  'FR',  'FC',  'BC']}
        {'code': 'quad',           'name': 'Quadro',          'layout': ['FL',  'FR',  'BL',  'BR']}
        #{'code': 'quad(side)',     'name': 'Quadro (side)',   'layout': ['FL',  'FR',  'SL',  'SR']}
        {'code': '3.1',            'name': '3.1',             'layout': ['FL',  'FR',  'FC',  'LFE']}
        #{'code': '5.0',            'name': '5.0 (back)',      'layout': ['FL',  'FR',  'FC',  'BL',  'BR']}
        {'code': '5.0(side)',      'name': '5.0 (side)',      'layout': ['FL',  'FR',  'FC',  'SL',  'SR']}
        {'code': '4.1',            'name': '4.1',             'layout': ['FL',  'FR',  'FC',  'LFE', 'BC']}
        {'code': '5.1',            'name': '5.1',             'layout': ['FL',  'FR',  'FC',  'LFE', 'BL',  'BR']}
        #{'code': '5.1(side)',      'name': '5.1 (side)',      'layout': ['FL',  'FR',  'FC',  'LFE', 'SL',  'SR']}
        {'code': '6.0',            'name': '6.0',             'layout': ['FL',  'FR',  'FC',  'BC',  'SL',  'SR']}
        #{'code': '6.0(front)',     'name': '6.0 (front)',     'layout': ['FL',  'FR',  'FLC', 'FRC', 'SL',  'SR']}
        {'code': 'hexagonal',      'name': 'Hexagonal',       'layout': ['FL',  'FR',  'FC',  'BL',  'BR',  'BC']}
        #{'code': '6.1',            'name': '6.1 (side)',      'layout': ['FL',  'FR',  'FC',  'LFE', 'BC',  'SL',  'SR']}
        {'code': '6.1',            'name': '6.1',             'layout': ['FL',  'FR',  'FC',  'LFE', 'BL',  'BR',  'BC']}
        {'code': '6.1(front)',     'name': '6.1 (front)',     'layout': ['FL',  'FR',  'LFE', 'FLC', 'FRC', 'SL',  'SR']}
        {'code': '7.0',            'name': '7.0',             'layout': ['FL',  'FR',  'FC',  'BL',  'BR',  'SL',  'SR']}
        #{'code': '7.0(front)',     'name': '7.0 (front)',     'layout': ['FL',  'FR',  'FC',  'FLC', 'FRC', 'SL',  'SR']}
        {'code': '7.1',            'name': '7.1',             'layout': ['FL',  'FR',  'FC',  'LFE', 'BL',  'BR',  'SL',  'SR']}
        #{'code': '7.1(wide)',      'name': '7.1 (wide)',      'layout': ['FL',  'FR',  'FC',  'LFE', 'BL',  'BR',  'FLC', 'FRC']}
        #{'code': '7.1(wide-side)', 'name': '7.1 (wide-side)', 'layout': ['FL',  'FR',  'FC',  'LFE', 'FLC', 'FRC', 'SL',  'SR']}
        {'code': 'octagonal',      'name': 'Octagonal',       'layout': ['FL',  'FR',  'FC',  'BL',  'BR',  'BC',  'SL',  'SR']}
        #{'code': 'downmix',        'name': 'Downmix',         'layout': ['DL',  'DR']}
    ]
    @audioChannels:
         'FL': 'front left'
         'FR': 'front right'
         'FC': 'front center'
         'LFE': 'low frequency'
         'BL': 'back left'
         'BR': 'back right'
         'FLC': 'front left-of-center'
         'FRC': 'front right-of-center'
         'BC': 'back center'
         'SL': 'side left'
         'SR': 'side right'
         'TC': 'top center'
         'TFL': 'top front left'
         'TFC': 'top front center'
         'TFR': 'top front right'
         'TBL': 'top back left'
         'TBC': 'top back center'
         'TBR': 'top back right'
         'DL': 'downmix left'
         'DR': 'downmix right'
         'WL': 'wide left'
         'WR': 'wide right'
         'SDL': 'surround direct left'
         'SDR': 'surround direct right'
         'LFE2': 'low frequency 2'

    constructor: ->
        @audioChannelSelectOptionsHtml = ''
        return

    reset: ->
        @audioChannelSelectOptionsHtml = ''
        return

    appendAudioChannelSelectOptions: (idx, iMedia, iTrack, iChannel) ->
        @audioChannelSelectOptionsHtml += '<option value="' + idx + '">' + padz(iMedia, 2) + '-t' + padz(iTrack, 2) + '-c' + padz(iChannel, 2) + '</option>'
        return

    updateAudioChannelSelect: ->
        layout = document.getElementById('pro-audio-layout-select').value
        console.log(layout)
        # Re-populate map list
        html = ''
        for pos, ci in AudioMan.audioLayouts[layout].layout
            html += '<tr id="map' + ci + '-' + pos + '" class="audio-out row0">'
            html += '<td class="audio-out col0">' + pos + '</td>'
            html += '<td class="audio-out col1">'
            html += '<select id="map' + ci + '-' + pos + '-select">' + @audioChannelSelectOptionsHtml + '</select>'
            html += '</td>'
        document.getElementById('pro-audio-layout-map').innerHTML = html
        return

    audioChannelsLayout: (channel_layout) ->
        if typeof channel_layout != 'string'
            return ''
        if channel_layout == 'mono'
            return 'FC'
        m = channel_layout.match(AudioMan.single_channel_re)
        if m != null and m.length == 2
            return m[1]
        channel_layout

    audioLayoutPullChannels: ->
        # Place channels sequence to layout, starting from current 'left' channel
        console.log g_InteractionPlayer
        if g_InteractionPlayer != null
            i = g_InteractionPlayer.LI
            layout = document.getElementById('pro-audio-layout-select').value
            for ci of AudioMan.audioLayouts[layout].layout
                id = 'map' + ci + '-' + AudioMan.audioLayouts[layout].layout[ci] + '-select'
                document.getElementById(id).value = i++
        return

class Astats
    constructor: (ast) ->
        @astats = ast

    format: ->
        if @astats != null
            res = 'Peak: ' + parseFloat(@astats['Peak level dB']).toFixed(2) + 'dB'
            res += '  RMS: ' + parseFloat(@astats['RMS peak dB']).toFixed(2)+'dB / '+parseFloat(@astats['RMS level dB']).toFixed(2) + 'dB'
        else
            res = 'No audio stats'
        return res

class InteractionsPage
    @hash: 'interactions'

    constructor: (app) ->
        console.log('== constructor InteractionsPage ==')
        @app = app
        @proposeAudioLang = null
        @interaction_initialized = false
        @interaction_selected = null        # Currently selected interaction's GUID
        @interaction_requested = null
        @interaction_internal = null
        @interactions = {}
        # @inter = null
        # @interaction_player = null
        @interaction_audioContext = new AudioContext
        # @api_rightholders_all = []
        # @api_rightholders = {}
        # @api_movies_all = []
        # @api_movies = {}
        @content_cards = [
            {title: 'dummy', id: '1'}
        ]
        @interaction_channelMerger = @interaction_audioContext.createChannelMerger(2)
        @interaction_channelMerger.connect @interaction_audioContext.destination

        @audioMan = new AudioMan
        @liveCrop = new LiveCrop
        @populateContentCardSelection
        return

    reset: ->


    updateAssetOut: ->
        # asset = @interaction_internal.asset
        # @interaction_internal.asset must be the same as @interactions[@interaction_selected].assetOut
        # Update crop dimensions
        @interaction_internal.update_asset(@liveCrop)
        return

    disableSelect: ->
        $('body').addClass('unselectable')
        return

    enableSelect: ->
        $('body').removeClass('unselectable')
        return

    enable: (param) ->
        if !@interaction_initialized
            @interaction_initialized = true
            $('#interaction-refresh').bind('click', @interactionsRefreshClick.bind(@))
            $('#pro-video-crop').bind('click', @restoreCropdetectClick.bind(@))
            # Populate layouts
            html = ''
            for layout, i in AudioMan.audioLayouts
                html += '<option value="' + i + '">' + layout.name + '</option>'
            layout_select = document.getElementById('pro-audio-layout-select')
            layout_select.innerHTML = html
            layout_select.value = 1
            $('#pro-audio-lang').bind 'change', ((a) ->
                @proposeAudioLang = a.target.value
                return
            ).bind(@)
            $('#pro-audio-layout-select').bind 'change', @audioMan.updateAudioChannelSelect.bind(@audioMan)
            $('#pro-movie-select').bind 'change', ((a) ->
                @proposeSelectMovie(a.target.value)
                return
            ).bind(@)
            $('#update-content-list').bind 'click', @getAllContentCards.bind(@)
            $('#pro-audio-layout-add').bind('click', (->
                # Add audio layout to output
                console.log('====================\npro-audio-layout-add')
                lang = document.getElementById('pro-audio-lang').value
                layout = document.getElementById('pro-audio-layout-select').value
                cl = []
                i = 0
                for pos, idx in AudioMan.audioLayouts[layout].layout
                    id = 'map' + idx + '-' + pos + '-select'
                    sel = document.getElementById(id).value
                    console.log('channel id: ' + id + 'channel selection: ' + sel)
                    cl.push sel
                    i++
                # console.log(cl)
                console.log('====================')
                @interaction_internal.addAudioOutput(lang, AudioMan.audioLayouts[layout].code, cl)
                return
            ).bind(@))
            $('#interaction-submit').bind 'click', (->
                @updateAssetOut()
                @app.ws_api_trix.request {
                    'method': 'interaction.submit'
                    'params':
                        'interaction': @interaction_selected
                        'asset': @interaction_internal.asset
                }, (answer) ->
                    console.log('submit_interaction response' + answer)
                    @interactionsRefreshClick
                    return
                return
            ).bind(@)
            $('#interaction-cancel').bind 'click', (->
                if !@interactions[@interaction_selected]
                    console.log 'No interaction selected'
                    return false
                @app.wsApiTrix.request {
                    'method': 'cancel_interaction'
                    'interaction': @interactions[@interaction_selected].id
                }, (answer) ->
                    console.log 'cancel_interaction response' + answer
                    return
                return
            ).bind(@)
            $('#interactions-unlock').bind 'click', (->
                @interaction_selected = null
                @app.wsApiTrix.request { 'method': 'cancel_all_interactions' }, (answer) ->
                    console.log 'cancel_all_interaction response', answer
                    return
                return
            ).bind(@)
            @makeDragX '#crop-x1', 0
            @makeDragX '#crop-x2', 1
            @makeDragY '#crop-y1', 2
            @makeDragY '#crop-y2', 3
        return

    makeDragX: (selector, ref) ->
        obj = $(selector)[0]
        parentX = absX(obj.parentNode)
        $('#crop-lines').on 'dragstart', selector, ->
            false
        $('#crop-lines').on 'mousedown', selector, ((e) ->
            @disableSelect()
            domEl = e.currentTarget
            ofs = e.pageX - parentX - (domEl.offsetLeft)
            @moveAtX e, domEl, parentX, ref
            document.onmousemove = ((e) ->
                @moveAtX e, domEl, parentX, ref, ofs
                return
            ).bind(this)
            domEl.onmouseup = (->
                document.onmousemove = null
                domEl.onmouseup = null
                @enableSelect()
                return
            ).bind(this)
            return
        ).bind(this)
        return

    moveAtX: (e, domEl, parentX, ref, ofs) ->
        x = e.pageX - parentX - ofs
        x = @liveCrop.updateLiveCropX(x, ref)
        domEl.style.left = x + 'px'
        return

    makeDragY: (selector, ref) ->
        obj = $(selector)[0]
        parentY = absY(obj.parentNode)
        $('#crop-lines').on 'dragstart', selector, ->
            false
        $('#crop-lines').on 'mousedown', selector, ((e) ->
            @disableSelect()
            domEl = e.currentTarget
            ofs = e.pageY - parentY - (domEl.offsetTop)
            @moveAtY e, domEl, parentY, ref
            document.onmousemove = ((e) ->
                @moveAtY e, domEl, parentY, ref, ofs
                return
            ).bind(this)
            domEl.onmouseup = (->
                document.onmousemove = null
                domEl.onmouseup = null
                @enableSelect()
                return
            ).bind(this)
            return
        ).bind(this)
        return

    moveAtY: (e, domEl, parentY, ref, ofs) ->
        y = e.pageY - parentY - ofs
        y = @liveCrop.updateLiveCropY(y, ref)
        domEl.style.top = y + 'px'
        return

    disable: (param) ->
        console.log 'interaction.js Out handler'
        if g_InteractionPlayer
            g_InteractionPlayer.pause()
        return

    interactionsRefreshClick: ->
        console.log 'interactionsRefreshClick'
        # TODO: check if there are some changes in currently loaded interactions
        for id of @interactions
            if @interactions[id]
                if @interactions[id].changed
                    console.log 'There are unsaved changes!'
                    return
        @app.ws_api_trix.request { 'method': 'interaction.getList', 'params': {'status': null, 'condition': null} }, @interactionsRefreshHandler.bind(@)
        return

    interactionsRefreshHandler: (msg) ->
        console.log 'interactionsRefreshHandler'
        answer = msg.result
        i = undefined
        if !answer
            console.log 'no results'
            return
        # Unbind all clicks
        for id of @interactions
            $('#' + id).unbind 'click'
        html = ''
        #<caption>Interactions</caption>
        html += '<tr>'
        cols = [
            'name'
            'guid'
            'priority'
            'assetIn'
        ]
        for col in cols
            html += '<th>' + col + '</th>'
        html += '</tr>'
        @interactions = {}
        for i, ans of answer
            ans.index = i
            console.log(ans)
            if ans.status == 1
                html += '<tr id="' + ans.guid + '" class="interaction row row' + i % 2 + '">'
            else if ans.guid == @interaction_selected
                html += '<tr id="' + ans.guid + '" class="interaction row row' + i % 2 + ' selected">'
            else
                html += '<tr id="' + ans.guid + '" class="interaction row locked">'
            for col in cols
                html += '<td>' + ans[col] + '</td>'
            html += '</tr>'
            @interactions[ans.guid] = ans
            i++
        document.getElementById('interaction-table').innerHTML = html
        for ans in answer
            $('#' + ans.guid).bind('click', @interactionClickRow.bind(@, ans.guid))
        return

    interactionClickRow: (inter_id) ->
        @interactionSelect(inter_id)
        return

    interactionSelect: (inter_id) ->
        console.log 'interactionSelect (' + inter_id + ')'
        if @interaction_selected == inter_id
            console.log 'already selected'
            return
        if @interactions[inter_id].status != 1
            console.log 'selected interaction status is ' + @interactions[inter_id].status
            return
        # Reset selection
        if @interaction_selected != null
            # TODO: delete @interaction_internal, player, etc.
#            document.getElementById(@interaction_selected).className = 'interaction row row' + inter.index % 2
            $('#' + @interaction_selected).removeClass('selected')
            @interaction_internal.update_asset(@liveCrop)
            @interactions[@interaction_selected].status = 1
#            inter = @interactions[@interaction_selected]
            @app.ws_api_trix.request({
                'method': 'interaction.unlock'
                'params': 'guid': @interaction_selected
            }, (answer) ->
                    console.log(answer)
                    return
            )
        @app.ws_api_trix.request({
            'method': 'interaction.lock'
            'params': 'guid': inter_id
        },  ((answer) ->
                answer.inter_id = inter_id
                @interaction_select_s2(answer)
            ).bind(@)
        )

    interaction_select_s2: (answer) ->
        console.log(answer)
        inter_id = answer.inter_id
        @interaction_selected = inter_id
        $('#' + @interaction_selected).addClass('selected')
        inter = @interactions[inter_id]
        if typeof(inter.assetIn) == 'string'
            # Request asset(s)
            @app.ws_api_trix.request({
                'method': 'asset.get_expanded'
                'params': 'guid': inter.assetIn
            }, @assetInRequestHandler.bind(@))
        else
            @interactionLoad()
        return

    assetInRequestHandler: (msg) ->
        console.log 'assetInRequestHandler'
        console.log msg
        inter = @interactions[@interaction_selected]
        # @interaction_selected = @interaction_requested
        # @inter = @interactions[@interaction_selected]
        # html = '<text>ID: ' + @interaction_selected + '</text>'
        inter.assetIn = msg.result
        if typeof(inter.assetOut) != 'string'
            # Clone assetIn to assetOut
            inter.assetOut = JSON.parse(JSON.stringify(inter.assetIn))
            inter.assetOut.mediaFiles = []
            inter.assetOut.mediaFilesExtra = []
            for mf in inter.assetIn.mediaFiles
                inter.assetOut.mediaFiles.push(mf.guid)
            if Object.prototype.toString.call(inter.assetIn.mediaFilesExtra) == '[object Array]'
                for mf in inter.assetIn.mediaFilesExtra
                    inter.assetOut.mediaFilesExtra.push(mf.guid)
        document.getElementById(inter.guid).className = 'interaction row row' + inter.index % 2 + ' selected'
        @interactionLoad()
        return

    interactionLoad: () ->
        inter = @interactions[@interaction_selected]
        if typeof(inter.assetIn) == 'string' or typeof(inter.assetOut) == 'string'
            return
        console.log('interactionLoad begin')
        delete @interaction_internal
        @interactionCreatePlayer()
        console.log('interactionLoad done')
        return

    interactionShowInfo: ->
        inter = @interactions[@interaction_selected]
        html = '<text>ID: ' + inter.guid + '</text>'
        document.getElementById('interaction-info').innerHTML = html
        return

    interactionCreatePlayer: ->
        console.log 'interactionCreatePlayer begin'
        doc_video = document.getElementById('interaction-video')
        inter = @interactions[@interaction_selected]
        if g_InteractionPlayer
            # Stop playback
            console.log('Stopping player')
            g_InteractionPlayer.stop()
            # Unbind all clicks
            $('#interaction_player_play').unbind 'click'
            $('#interaction_player_pause').unbind 'click'
            $('#interaction_player_setBlockIn').unbind 'click'
            $('#interaction_player_setBlockRemove').unbind 'click'
            $('#interaction_player_setBlockOut').unbind 'click'
            $('#interaction_player_setProgramIn').unbind 'click'
            $('#interaction_player_setProgramOut').unbind 'click'

            $('#interaction_player_jumpLeft').unbind 'click'
            $('#interaction_player_jumpLeft30').unbind 'click'
            $('#interaction_player_jumpLeft05').unbind 'click'
            $('#interaction_player_jumpRight05').unbind 'click'
            $('#interaction_player_jumpRight30').unbind 'click'
            $('#interaction_player_jumpRight').unbind 'click'

            $('#interaction_player_cueBlockIn').unbind 'click'
            $('#interaction_player_cueBlockOut').unbind 'click'
            $('#interaction_player_cueProgramIn').unbind 'click'
            $('#interaction_player_cueProgramOut').unbind 'click'
            $('#interaction_player_decreaseDelay').unbind 'click'
            $('#interaction_player_increaseDelay').unbind 'click'
            $('#interaction_player_decreaseDelay1s').unbind 'click'
            $('#interaction_player_increaseDelay1s').unbind 'click'
            $('#interaction_player_addSyncPoint').unbind 'click'

            $('#pro-audio-layout-pull').unbind 'click'
            g_InteractionPlayer = null

        html = ''
        audio_elements = []
        video_elements = []
        sub_elements = []

        delay_ms_v = 0.0
        @audioMan.reset()
        count_ac = 0
        count_vc = 0
        count_sc = 0
        cc = 0

        vInfo = null

        # Map media files
        mf_map = {}
        mfex_map = {}
#        coll_map = {}
        for mf in inter.assetIn.mediaFiles
            mf_map[mf.guid] = mf
        for mf in inter.assetIn.mediaFilesExtra
            mfex_map[mf.guid] = mf
#        for coll in inter.assetIn.collectors
#            coll_map[coll.guid] = coll

        # Compile channel map, copy preview urls
        # Abs channel index to track:channel map
        audio_channels_map_to_tracks = []
        ti = 0
        for mf in inter.assetIn.mediaFiles
            for track in mf.audioTracks
                for ci in [0...track.channels]
                    audio_channels_map_to_tracks.push([ti, ci])
                tid = track.extract
                if mfex_map.hasOwnProperty(tid)
                    track.previews = mfex_map[tid].audioTracks[0].previews
                ti++
            for track in mf.subTracks
                tid = track.extract
                if mfex_map.hasOwnProperty(tid)
                    track.previews = mfex_map[tid].subTracks[0].previews

        # Enumerate original media files
        for mf, mi in inter.assetIn.mediaFiles
            # count tracks and channels to set file rowspan (total channel count in file)
            ct = 0
            for track in mf.audioTracks
                ct += track.channels
            ct += mf.videoTracks.length
            ct += mf.subTracks.length
            if ct == 0
                continue

            # File part
            id = 'src-' + padz(mi, 2) + '" rowspan="' + ct
            html_f = '<td id="' + id + '" class="src row' + mi % 2 + ' col0">file</td>'

            # Tracks part
            for track, ti in mf.videoTracks
                if vInfo == null
                    vInfo = track
                else
                    throw 'More than 1 video tracks!'
                delay_ms_v = parseInt(1000.0 * track.start_time)
                id = 'src-' + padz(mi, 2) + '-t' + padz(ti, 2)
                channel_layout = 'mono'
                video_src = document.createElement('source')
                video_src.type = 'video/mp4'
                video_src.src = track.previews[0]
                video_elements.push video_src
                # Add row
                html += '<tr class="src">'
                html += html_f
                html += '<td id="' + id + '" rowspan="' + 1 + '" class="src row' + ti % 2 + ' col1">video</td>'
                html += '<td id="' + id + '" class="src row' + cc % 2 + ' col2">' + channel_layout + '</td>'
                html += '</tr>'
                html_f = ''
                count_vc++
                cc++
            for track, ti in mf.audioTracks
                delay_ms_a = parseInt(1000.0 * track.start_time)
                channels = track.channels
                channel_layout = track.channel_layout
                id = 'src-' + padz(mi, 2) + '-t' + padz(ti, 2)
                html_t = '<td id="' + id + '" rowspan="' + channels + '" class="src row' + ti % 2 + ' col1">audio</td>'
                ast = track['astats']
                console.log 'astats: '
                console.log ast
                for ci in [0...track.channels]
                    id = 'src-' + padz(mi, 2) + '-t' + padz(ti, 2) + '-c' + padz(ci, 2)
                    # Create playable audio
                    snd = new Audio()
                    src = document.createElement('source')
                    src.type = 'audio/mp4'
                    src.src = track.previews[ci]
                    snd.appendChild(src)
                    node = @interaction_audioContext.createMediaElementSource(snd)
                    ae =
                        'abs': count_ac
                        'html-id': id
                        'audio': snd
                        'node': node
                        'delay_ms': delay_ms_a - delay_ms_v
                        'sync1': null
                        'sync2': null
                        'track': ti
                        'channel': ci
                    if ast == undefined
                        ae.astats_channel = new Astats(null)
                        ae.astats_all = new Astats(null)
                    else
                        ae.astats_channel = new Astats(ast[ci+1])
                        ae.astats_all = new Astats(ast.all)

                    # if 'start_time' of info[mi][ttype][ti]
                    #     st = parseFloat(+info[mi][ttype][ti].start_time)
                    #     if !isNaN(st)
                    #         ae.delay_ms = Math.round(1000 * st)
                    audio_elements.push ae
                    @audioMan.appendAudioChannelSelectOptions count_ac, mi, ti, ci
                    count_ac++
                    # Add row to Sources table
                    html += '<tr class="src">'
                    html += html_f
                    html += html_t
                    html += '<td id="' + id + '" class="src row' + cc % 2 + ' col2">' + @audioMan.audioChannelsLayout(channel_layout) + ' #' + ci + '</td>'
                    html += '</tr>'
                    html_f = ''
                    html_t = ''
                    cc++
                    ci++
                # ti++
            for track, ti in mf.subTracks
                id = 'sub-abs-' + padz(count_sc, 2)
                codec = track.codec

                sub = document.createElement("track")
                sub.kind = "captions"
                sub.label = "English"
                sub.srclang = "en"
                sub.src = track.previews[0]

                sub_elements.push({node: sub, 'html-id': id})
                # Add row
                html += '<tr class="src">'
                html += html_f
                html += '<td rowspan="' + 1 + '" class="src row' + ti % 2 + ' col1">subtitles</td>'
                html += '<td id="' + id + '" class="src row' + cc % 2 + ' col2">' + codec + '</td>'
                html += '</tr>'
                html_f = ''
                count_sc++
                cc++
            mi++
        document.getElementById('src-map').innerHTML = html
        @audioMan.updateAudioChannelSelect()

        # Bind clicks
        g_InteractionPlayer = new InteractionPlayer(document.getElementById('interaction-video'),
                                                    video_elements,
                                                    audio_elements,
                                                    sub_elements,
                                                    @interaction_channelMerger,
                                                    inter.assetOut.videoStreams[0].program_in,
                                                    inter.assetOut.videoStreams[0].program_out)
        for ae, ci in audio_elements
            $('#' + ae['html-id']).bind 'click', g_InteractionPlayer.selectChannel.bind(g_InteractionPlayer, ci)
        for se, ci in sub_elements
            $('#' + se['html-id']).bind 'click', g_InteractionPlayer.selectSubtitles.bind(g_InteractionPlayer, ci)

        # Video crop setup
        vCrop = inter.assetOut.videoStreams[0].cropdetect

        console.log vCrop
        console.log vInfo

        @liveCrop.setVideoSrcDimensions vInfo.width, vInfo.height
        @liveCrop.setVideoSrcCrop vCrop.x, vCrop.x + vCrop.w, vCrop.y, vCrop.y + vCrop.h
        @liveCrop.snapLiveCrop 4
        @liveCrop.updateCropString()
        @liveCrop.positionCropLines()
        $('#interaction_player_play').bind 'click', g_InteractionPlayer.play.bind(g_InteractionPlayer)
        $('#interaction_player_pause').bind 'click', g_InteractionPlayer.pause.bind(g_InteractionPlayer)
        $('#interaction_player_setBlockIn').bind 'click', g_InteractionPlayer.setBlockIn.bind(g_InteractionPlayer)
        $('#interaction_player_setBlockRemove').bind 'click', g_InteractionPlayer.blockRemove.bind(g_InteractionPlayer)
        $('#interaction_player_setBlockOut').bind 'click', g_InteractionPlayer.setBlockOut.bind(g_InteractionPlayer)
        $('#interaction_player_setProgramIn').bind 'click', g_InteractionPlayer.setProgramIn.bind(g_InteractionPlayer)
        $('#interaction_player_setProgramOut').bind 'click', g_InteractionPlayer.setProgramOut.bind(g_InteractionPlayer)

        $('#interaction_player_jumpLeft30').bind('click', ( -> g_InteractionPlayer.cueOffset(-30.0)).bind(g_InteractionPlayer))
        $('#interaction_player_jumpLeft05').bind('click', ( -> g_InteractionPlayer.cueOffset(-5.0)).bind(g_InteractionPlayer))
        $('#interaction_player_jumpRight05').bind('click', ( -> g_InteractionPlayer.cueOffset(5.0)).bind(g_InteractionPlayer))
        $('#interaction_player_jumpRight30').bind('click', ( -> g_InteractionPlayer.cueOffset(30.0)).bind(g_InteractionPlayer))

        $('#interaction_player_jumpLeft').bind 'click', g_InteractionPlayer.cueLeft.bind(g_InteractionPlayer)
        $('#interaction_player_jumpRight').bind 'click', g_InteractionPlayer.cueRight.bind(g_InteractionPlayer)

        $('#interaction_player_cueBlockIn').bind 'click', g_InteractionPlayer.cueBlockIn.bind(g_InteractionPlayer)
        $('#interaction_player_cueBlockOut').bind 'click', g_InteractionPlayer.cueBlockOut.bind(g_InteractionPlayer)
        $('#interaction_player_cueProgramIn').bind 'click', g_InteractionPlayer.cueProgramIn.bind(g_InteractionPlayer)
        $('#interaction_player_cueProgramOut').bind 'click', g_InteractionPlayer.cueProgramOut.bind(g_InteractionPlayer)
        $('#interaction_player_decreaseDelay').bind 'click', g_InteractionPlayer.decreaseDelay.bind(g_InteractionPlayer)
        $('#interaction_player_increaseDelay').bind 'click', g_InteractionPlayer.increaseDelay.bind(g_InteractionPlayer)
        $('#interaction_player_decreaseDelay1s').bind 'click', g_InteractionPlayer.decreaseDelay1s.bind(g_InteractionPlayer)
        $('#interaction_player_increaseDelay1s').bind 'click', g_InteractionPlayer.increaseDelay1s.bind(g_InteractionPlayer)
        $('#interaction_player_addSyncPoint').bind 'click', g_InteractionPlayer.addSyncPoint.bind(g_InteractionPlayer)

        $('#pro-audio-layout-pull').bind('click', @audioMan.audioLayoutPullChannels)


        @interaction_internal = new InteractionInternal(inter.assetOut, audio_channels_map_to_tracks, g_InteractionPlayer)
        @interaction_internal.showAudioOutputs()
        @interaction_internal.audioRemoveBindAll()
        @interactionShowInfo()

        console.log 'interactionCreatePlayer done'
        return

    restoreCropdetectClick: () ->
        if @interaction_selected == null
            return
        inter = @interactions[@interaction_selected]
        vCrop = inter.assetIn.videoStreams[0].cropdetect
        @liveCrop.setVideoSrcCrop vCrop.x, vCrop.x + vCrop.w, vCrop.y, vCrop.y + vCrop.h
        @liveCrop.updateCropString()
        @liveCrop.positionCropLines()
        return

    proposeSelectMovie: (index) ->
        @interaction_internal.asset.name = @content_cards[index].title
        @interaction_internal.asset.programId = @content_cards[index].id
        @interaction_internal.showMovie()
        return

    getAllContentCards: ->
        console.log 'Get all content cards'
        @content_cards = [
            {title: 'Sunrise', id: '47504'}
            {title: 'Moonshine', id: '124385'}
            {title: 'Sun & Moon ', id: '180685'}
            {title: 'Sunset', id: '139328'}
            {title: 'Sunshine', id: '16640'}
        ]
        @populateContentCardSelection()
        return

    populateContentCardSelection: ->
        html = ''
        for c, i in @content_cards
            html += '<option value="' + i + '">' + c.title + ' (' + c.id + ')' + '</option>'
        document.getElementById('pro-movie-select').innerHTML = html

    getAllMoviesData: ->
        console.log 'Get All Movies #1'
        if @app.wsNapi.state == 'authorized'
            @app.wsNapi.request {
                'method': 'rightholders_all'
                'params': {}
            }, @gamdRightholdersAll.bind(this)
        else
            @app.setMainStatus 'Not authorized'
        return

    gamdRightholdersAll: (m) ->
        console.log 'Get All Movies #2'
        @api_rightholders_all = m.result.ids
        # Continue requesting rightholders
        @app.setMainStatus 'Requesting rightholders data...'
        @app.wsNapi.request {
            'method': 'rightholders'
            'params': 'ids': @api_rightholders_all
        }, @gamdRightholders.bind(this)
        return

    gamdRightholders: (m) ->
        console.log 'Get All Movies #3'
        @api_rightholders = {}
        i = 0
        while i < m.result.length
            # Rebuild from {"id": x, "name": "Warner Bros. Entertainment, Inc."}
            # to x: {'name': 'Warner Bros. Entertainment, Inc.', 'legacy': 'Warner_Bros_Entertainment_Inc', 'alias': 'WB'}
            rhId = m.result[i].id
            rhName = m.result[i].name
            rhAlias = undefined
            rhLegacy = legalizeName(rhName)
            if rhName of Rightholders.aliases
                rhAlias = Rightholders.aliases[rhName]
            else
                rhAlias = rhLegacy
            @api_rightholders[rhId] =
                'name': rhName
                'legacy': rhLegacy
                'alias': rhAlias
            i++
        # Continue requesting movies IDs
        @app.setMainStatus 'Requesting list of movies...'
        @app.wsNapi.request {
            'method': 'movies_all'
            'params': {}
        }, gamdMoviesAll
        return

    gamdMoviesAll: (m) ->
        console.log 'Get All Movies #4'
        @api_movies_all = m.result.ids
        # Continue requesting movies data
        @app.setMainStatus 'Requesting movies data...'
        @app.wsNapi.request {
            'method': 'movies_extra'
            'params': 'ids': @api_movies_all
        }, gamdMoviesExtra
        return

    gamdMoviesExtra: (m) ->
        console.log 'Get All Movies #5'
        @app.setMainStatus 'Rebuild data...'
        @api_movies = {}
        @api_movies_all = []
        i = 0
        while i < m.result.length
            # Rebuild data
            moStudio = m.result[i].rightholder_ids[0]
            if !@api_movies.hasOwnProperty(moStudio)
                @api_movies[moStudio] = {}
            @api_movies[moStudio][m.result[i].id] =
                'slug': m.result[i].slug
                'guid': m.result[i].id_guid
                'title': m.result[i].title
                'original_title': m.result[i].original_title
                'title_legacy': legalizeName(m.result[i].title)
                'original_title_legacy': legalizeName(m.result[i].original_title)
                'status': m.result[i].status
                'video': m.result[i].video
            i++
        @buildProposedMovies()
        return

    buildProposedMovies: ->
        `var st`
        # Build sorted list of proposed movies
        if @interaction_selected == null
            return
        tmplist = undefined
        titles = []
        fname = @interactions[@interaction_selected].data_in.source_filenames[0]
        studio = @interactions[@interaction_selected].data_in.studio
        ot = undefined
        otl = undefined
        guid = undefined
        studioList = []
        i = 0
        if studio
            # Search studio index
            for st of @api_rightholders
                if @api_rightholders[st].alias == studio
                    studio = st
                    break
            studioList.push studio
        for st of @api_movies
            if st != studio
                studioList.push st
        i = 0
        while i < studioList.length
            tmplist = []
            studio = studioList[i]
            for id of @api_movies[studio]
                ot = @api_movies[studio][id].original_title
                otl = @api_movies[studio][id].original_title_legacy
                guid = @api_movies[studio][id].guid
                tmplist.push [
                    simpleStringDistance(otl, fname)
                    studio
                    ot
                    id
                    guid
                    otl
                ]
            tmplist.sort (a, b) ->
                a[0] - (b[0])
            titles.push tmplist
            i++
        # Build <select>
        html = ''
        @api_movies_all = []
        i = 0
        while i < titles.length
            j = 0
            while j < titles[i].length
                html += '<option value="' + @api_movies_all.length + '">' + titles[i][j][2] + ' (' + @api_rightholders[titles[i][j][1]].alias + ')' + '</option>'
                @api_movies_all.push titles[i][j]
                j++
            i++
        document.getElementById('pro-movie-select').innerHTML = html
        @proposeSelectMovie 0
        @app.setMainStatus 'Ok'
        return

    # function updateTime () {
    #    this.interaction_player.doc_currentTime.innerHTML = this.interaction_player.video.currentTime.toFixed(2);
    #    this.interaction_player.timeline_pb.style.width = 100*(this.interaction_player.video.currentTime/this.interaction_player.video.duration) + '%';
    #    this.interaction_player.synchronize();
    # }
