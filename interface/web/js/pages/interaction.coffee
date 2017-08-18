'use strict'

$ = require('jquery')
LiveCrop = require('./pages/ui/live_crop')
InteractionPlayer = require('./pages/ui/interaction_player')
InteractionInternal = require('./models/InteractionInternal')
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

zeroez = '0000000000000000'

zpad = (strnum, size) ->
    # Up to 16 leading zeroes
    if strnum.length < size
        strnum = zeroez.substring(0, size - (strnum.length)) + strnum
    strnum

odev = (number) ->
    if number % 2 then 'odd' else 'even'

createStyleSequence = (baseName, h, s, l, a, hH, sH, lH, aH, rotOddEvenH, gainOddEvenL, steps) ->
    css = ''
    ho = 0
    lig = 0
    # var sat = 0;
    # var oel = 0;
    i = 0
    while i < steps
        oe = i % 2
        ho = (h + (i - oe) * 360 / steps + rotOddEvenH * oe) % 360
        lig = l + gainOddEvenL * oe
        css += '.' + baseName + padz(i, 2) + '{background-color:hsla(' + ho + ',' + s + '%,' + lig + '%,' + a + ');} '
        ho = (hH + (i - oe) * 360 / steps + rotOddEvenH * oe) % 360
        lig = lH + gainOddEvenL * oe
        css += '.' + baseName + padz(i, 2) + ':hover{background-color:hsla(' + ho + ',' + sH + '%,' + lig + '%,' + aH + ');} '
        i++
    style = document.createElement('style')
    if style.styleSheet
        style.styleSheet.cssText = css
    else
        style.appendChild document.createTextNode(css)
    document.getElementsByTagName('head')[0].appendChild style
    return


class AudioMan
    constructor: ->
        @audioChannelSelectOptionsHtml = ''

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

    reset: ->
        @audioChannelSelectOptionsHtml = ''
        return

    appendAudioChannelSelectOptions: (idx, iMedia, iTrack, iChannel) ->
        @audioChannelSelectOptionsHtml += '<option value="' + idx + '">' + padz(iMedia, 2) + '-t' + padz(iTrack, 2) + '-c' + padz(iChannel, 2) + '</option>'
        return

    updateAudioChannelSelect: ->
        layout = document.getElementById('pro-audio-layout-select').value
        console.log layout
        # Re-populate map list
        html = ''
        for ci of @audioLayouts[layout].layout
            pos = @audioLayouts[layout].layout[ci]
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
        m = channel_layout.match(@single_channel_re)
        if m != null and m.length == 2
            return m[1]
        channel_layout

    audioLayoutPullChannels: ->
        # Place channels sequence to layout, starting from current 'left' channel
        if interaction_player != null
            i = interaction_player.LI
            layout = document.getElementById('pro-audio-layout-select').value
            for ci of @audioLayouts[layout].layout
                id = 'map' + ci + '-' + @audioLayouts[layout].layout[ci] + '-select'
                document.getElementById(id).value = i++
        return


class InteractionPage
    @hash: 'interaction'

    constructor: (app) ->
        @app = app
        @proposeAudioLang = null
        @interaction_initialized = false
        @interaction_selected = null
        @interaction_requested = null
        @interaction_internal = null
        @interactions = {}
        @inter = null
        @interaction_player = null
        @interaction_audioContext = new AudioContext
        @api_rightholders_all = []
        @api_rightholders = {}
        @api_movies_all = []
        @api_movies = {}
        @interaction_channelMerger = @interaction_audioContext.createChannelMerger(2)
        @interaction_channelMerger.connect @interaction_audioContext.destination

        @audioMan = new AudioMan()
        $('#pro-audio-layout-pull').bind 'click', @audioMan.audioLayoutPullChannels.bind(@audioMan)
        @liveCrop = new LiveCrop
        return

    updateInteractionDataOut: ->
        data = @interactions[@interaction_selected].data_out
        # Video part
        # Copy crop data
        data.program.video.crop.w = liveCrop.liveCrop[1] - (liveCrop.liveCrop[0])
        data.program.video.crop.h = liveCrop.liveCrop[3] - (liveCrop.liveCrop[2])
        data.program.video.crop.x = liveCrop.liveCrop[0]
        data.program.video.crop.y = liveCrop.liveCrop[2]
        # Program in/out/duration
        data.video.map.in = @interaction_player.timeStart
        data.video.map.out = @interaction_player.timeEnd
        # Sample fragments considering program start time
        data.sample = []
        i = 0
        while i < @interaction_player.bars.length
            bar = @interaction_player.bars[i]
            data.sample.push [
                bar.timeStart - (@interaction_player.timeStart)
                bar.timeEnd - (bar.timeStart)
            ]
            i++
        # Audio part
        # Color generation
        #var fileCWS = 6;
        #var trackCWS = 4;
        #var channelCWS = 8;
        # Creating styles
        #createStyleSequence('src-file-map.s', 0, 8, 16, 1.0, 0, 16, 24, 1.0, fileCWS);
        #                                          hue   sat  light alpha  hue   sat  light alpha   OEH   OEL
        #createStyleSequence('src-file-map.s',         0,   12,   15,  1.0,    0,   16,   20,  1.0,  180,  2.0, fileCWS);
        #createStyleSequence('src-track.t',          120,    8,   24,  0.5,  180,    8,   32, 0.75,  180,  2.0, trackCWS);
        #createStyleSequence('src-audio-channel.c',    0,    4,   16,  0.5,    0,    4,    0, 0.75,  180,  6.0, channelCWS);
        return

    disableSelect: ->
        $('body').addClass 'unselectable'
        return

    enableSelect: ->
        $('body').removeClass 'unselectable'
        return

    enable: (param) ->
        if !@interaction_initialized
            @interaction_initialized = true
            $('#interaction-refresh').bind 'click', @interactionsRefreshClick.bind(this)
            # Populate layouts
            html = ''
            i = 0
            while i < AudioMan.audioLayouts.length
                html += '<option value="' + i + '">' + AudioMan.audioLayouts[i].name + '</option>'
                i++
            document.getElementById('pro-audio-layout-select').innerHTML = html
            $('#pro-audio-lang').bind 'change', ((a) ->
                @proposeAudioLang = a.target.value
                return
            ).bind(this)
            $('#pro-audio-layout-select').bind 'change', @audioMan.updateAudioChannelSelect.bind(@audioMan)
            $('#pro-movie-select').bind 'change', ((a) ->
                @proposeSelectMovie a.target.value
                return
            ).bind(this)
            $('#napi-register').bind 'click', @getAllMoviesData.bind(this)
            $('#pro-audio-layout-add').bind 'click', (->
                `var i`
                # Add audio layout to output
                lang = document.getElementById('pro-audio-lang').value
                layout = document.getElementById('pro-audio-layout-select').value
                cl = []
                i = 0
                while i < AudioMan.audioLayouts[layout].layout.length
                    pos = AudioMan.audioLayouts[layout].layout[i]
                    id = 'map' + i + '-' + pos + '-select'
                    sel = document.getElementById(id).value
                    cl.push sel
                    i++
                @interactions[@interaction_selected].addAudioOutput lang, AudioMan.audioLayouts[layout].code, cl
                return
            ).bind(this)
            $('#interaction-submit').bind 'click', (->
                if !@interactions[@interaction_selected]
                    console.log 'No interaction selected'
                    return false
                @updateInteractionDataOut()
                @app.wsApiTrix.request {
                    'method': 'submit_interaction'
                    'interaction': @interactions[@interaction_selected].data_out
                }, (answer) ->
                    console.log 'submit_interaction response' + answer
                    return
                return
            ).bind(this)
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
            ).bind(this)
            $('#interactions-unlock').bind 'click', (->
                @interaction_selected = null
                @app.wsApiTrix.request { 'method': 'cancel_all_interactions' }, (answer) ->
                    console.log 'cancel_all_interaction response', answer
                    return
                return
            ).bind(this)
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
        if @interaction_player
            @interaction_player.pause()
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
            html += '<tr id="' + ans.guid + '" class="interaction row row' + i % 2 + '">'
            for col in cols
                html += '<td>' + ans[col] + '</td>'
            html += '</tr>'
#            @interactions[answer[i].id] = new InteractionInternal(answer[i], @interaction_player)
#            inter = new Interaction()
#            UpdateObjectWithJSON(inter, ans)
            @interactions[ans.guid] = ans
            i++
        document.getElementById('interaction-table').innerHTML = html
        for ans in answer
            $('#' + ans.guid).bind 'click', @interactionClickRow.bind(@, ans.guid)
        return

    interactionClickRow: (inter_id) ->
        @interactionSelect inter_id
        return

    interactionSelect: (inter_id) ->
        console.log 'interactionSelect (' + inter_id + ')'
        if @interaction_selected == inter_id
            console.log 'already selected'
            return
        # Reset selection
        if @interaction_selected != null
            # TODO: delete @interaction_internal
            isel = @interactions[@interaction_selected]
            document.getElementById(isel.guid).className = 'interaction row row' + isel.index % 2
            @interaction_selected = null
        inter = @interactions[inter_id]
        if typeof inter.assetIn == 'string'
            # Request asset
            @interaction_requested = inter_id
            @app.ws_api_trix.request {
                'method': 'asset.get_expanded'
                'params': 'guid': inter.assetIn
            }, @assetRequestHandler.bind(@)
        else
            @interactionLoad(inter.assetIn)
#            @interactionCreatePlayer()
#            inter.showAudioOutputs()
#            @interactionShowInfo inter
        return

    assetRequestHandler: (msg) ->
        console.log 'assetRequestHandler'
        console.log msg
        @interaction_selected = @interaction_requested
        @inter = @interactions[@interaction_selected]
        html = '<text>ID: ' + @interaction_selected + '</text>'
        @inter.assetIn = msg.result
        document.getElementById(@inter.guid).className = 'interaction row row' + @inter.index % 2 + ' selected'
#        inter.data_out.video = inter.data_in.video
        @interactionLoad()
#        @interactionCreatePlayer()
#        inter.showAudioOutputs()
#        @interactionShowInfo inter
        return

    interactionLoad: () ->
        delete @interaction_internal
        @interactionCreatePlayer()
        @interaction_internal = new InteractionInternal(@inter.assetIn, @interaction_player)
        @interaction_internal.showAudioOutputs()
        @interactionShowInfo
        return

    interactionShowInfo: ->
        inter = @interactions[@interaction_selected]
        html = '<text>ID: ' + inter.guid + '</text>'
        if typeof inter.data_in != 'undefined' and inter.data_in != null
            arr = Object.keys(inter.data_in)
            arr.sort()
            i = 0
            while i < arr.length
                key = arr[i]
                outputData = ''
                if typeof inter.data_in[key] == 'object'
                    outputData = JSON.stringify(inter.data_in[key])
                else
                    outputData = inter.data_in[key]
                html += '<br/><text>' + key + ': ' + outputData + '</text>'
                i++
        document.getElementById('interaction-info').innerHTML = html
        return

    interactionCreatePlayer: () ->
#        data = inter.data_in
#        info = data.infos
        # TODO: data['program']['video']['crop'] contains crop data, use it to position crop frame
        console.log 'initialize player'
        if @interaction_player
            # Stop playback
            @interaction_player.stop()
            # Unbind all clicks
            $('#interaction_player_play').unbind 'click'
            $('#interaction_player_pause').unbind 'click'
            $('#interaction_player_setBlockIn').unbind 'click'
            $('#interaction_player_setBlockRemove').unbind 'click'
            $('#interaction_player_setBlockOut').unbind 'click'
            $('#interaction_player_setProgramIn').unbind 'click'
            $('#interaction_player_setProgramOut').unbind 'click'
            $('#interaction_player_cueBlockIn').unbind 'click'
            $('#interaction_player_cueBlockOut').unbind 'click'
            $('#interaction_player_cueProgramIn').unbind 'click'
            $('#interaction_player_cueProgramOut').unbind 'click'
            $('#interaction_player_decreaseDelay').unbind 'click'
            $('#interaction_player_increaseDelay').unbind 'click'
            delete @interaction_player
        html = ''
        audio_elements = []
        video_elements = []
        @audioMan.reset()
#        count_t = 0
        count_ac = 0
        count_vc = 0
        cc = 0

        debugger
        # Enumerate media files
        for mf, mi in @inter.assetIn.mediaFiles

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
                id = 'src-' + padz(mi, 2) + '-t' + padz(ti, 2)
                channel_layout = 'mono'
                video_src = document.createElement('source')
                video_src.type = 'video/mp4'
                video_src.src = track.refs[0]
                video_elements.push video_src
                # Add row
                html += '<tr class="src">'
                html += html_f
                html += '<td id="' + id + '" rowspan="' + 1 + '" class="src row' + ti % 2 + ' col1">video</td>'
                html += '<td id="' + id + '" class="src row' + cc % 2 + ' col2">' + channel_layout + '</td>'
                html += '</tr>'
                html_f = ''
                count_vc++
#                count_t++
                cc++
            for track, ti in mf.audioTracks
                channels = track.channels
                channel_layout = track.channel_layout
                id = 'src-' + padz(mi, 2) + '-t' + padz(ti, 2)
                html_t = '<td id="' + id + '" rowspan="' + channels + '" class="src row' + ti % 2 + ' col1">audio</td>'
                for ci in [0...track.channels]
                    id = 'src-' + padz(mi, 2) + '-t' + padz(ti, 2) + '-c' + padz(ci, 2)
                    # Create playable audio
                    snd = new Audio
                    src = document.createElement('source')
                    src.type = 'audio/mp4'
                    src.src = track.refs[ci]
                    snd.appendChild src
                    node = @interaction_audioContext.createMediaElementSource(snd)
                    ae =
                        'abs': count_ac
                        'html-id': id
                        'audio': snd
                        'node': node
                        'delay_ms': 0
#                        'file': fi
                        'track': ti
                        'channel': ci
#                    if 'start_time' of info[mi][ttype][ti]
#                        st = parseFloat(+info[mi][ttype][ti].start_time)
#                        if !isNaN(st)
#                            ae.delay_ms = Math.round(1000 * st)
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
                ti++
            mi++
        document.getElementById('src-map').innerHTML = html
        @audioMan.updateAudioChannelSelect()
        # Bind clicks
        @interaction_player = new InteractionPlayer(document.getElementById('interaction-video'), video_elements, audio_elements, @interaction_channelMerger)
        for ae, ci in audio_elements
            $('#' + ae['html-id']).bind 'click', @interaction_player.selectChannel.bind(@interaction_player, ci)
        vCrop = data.program.video.crop
        vMap = data.program.video.map[0]
        vInfo = data.infos[vMap.ii]
        console.log vCrop
        console.log vMap
        console.log vInfo
        @liveCrop.setVideoSrcDimensions vInfo.video[vMap.ti].ffprobe.width, vInfo.video[vMap.ti].ffprobe.height
        @liveCrop.setVideoSrcCrop vCrop.x, vCrop.x + vCrop.w, vCrop.y, vCrop.y + vCrop.h
        @liveCrop.snapLiveCrop 8
        @liveCrop.updateCropString()
        @liveCrop.positionCropLines()
        $('#interaction_player_play').bind 'click', @interaction_player.play.bind(@interaction_player)
        $('#interaction_player_pause').bind 'click', @interaction_player.pause.bind(@interaction_player)
        $('#interaction_player_setBlockIn').bind 'click', @interaction_player.setBlockIn.bind(@interaction_player)
        $('#interaction_player_setBlockRemove').bind 'click', @interaction_player.blockRemove.bind(@interaction_player)
        $('#interaction_player_setBlockOut').bind 'click', @interaction_player.setBlockOut.bind(@interaction_player)
        $('#interaction_player_setProgramIn').bind 'click', @interaction_player.setProgramIn.bind(@interaction_player)
        $('#interaction_player_setProgramOut').bind 'click', @interaction_player.setProgramOut.bind(@interaction_player)
        $('#interaction_player_cueBlockIn').bind 'click', @interaction_player.cueBlockIn.bind(@interaction_player)
        $('#interaction_player_cueBlockOut').bind 'click', @interaction_player.cueBlockOut.bind(@interaction_player)
        $('#interaction_player_cueProgramIn').bind 'click', @interaction_player.cueProgramIn.bind(@interaction_player)
        $('#interaction_player_cueProgramOut').bind 'click', @interaction_player.cueProgramOut.bind(@interaction_player)
        $('#interaction_player_decreaseDelay').bind 'click', @interaction_player.decreaseDelay.bind(@interaction_player)
        $('#interaction_player_increaseDelay').bind 'click', @interaction_player.increaseDelay.bind(@interaction_player)
        return

    proposeSelectMovie: (index) ->
        @interactions[@interaction_selected].data_out.movie = @api_movies_all[index][2]
        @interactions[@interaction_selected].data_out.studio = @api_rightholders[@api_movies_all[index][1]].alias
        @interactions[@interaction_selected].data_out.movie_guid = @api_movies_all[index][4]
        @interactions[@interaction_selected].showMovie()
        return

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
    #InteractionPage.name = 'interaction';
    # })();
    # app.handlers([
    #     function() { var $page = $(this); return InteractionPage.interactionHandlerIn; },
    #     function() { var $page = $(this); return InteractionPage.interactionHandlerOut; }
    # ]);
#module.exports = InteractionPage
