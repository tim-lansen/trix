#'use strict'
#$ = require('jquery')
#Timeline = require('./Timeline')

class InteractionPlayer
    constructor: (video_object, video_elements, audio_elements, sub_elements, interaction_channelMerger, program_in, program_out) ->
        @video = video_object
        @video.appendChild video_elements[0]
        @audio_inter = audio_elements
        @subtitles = sub_elements
        @interaction_channelMerger = interaction_channelMerger
        @timeStart = program_in
        @timeEnd = program_out
        @duration = program_out - program_in
        $(@video).one 'loadedmetadata', ((elm) ->
            console.log('InteractionPlayer.video loaded')
            console.log(elm.target)
            @duration = elm.currentTarget.duration
            if @timeEnd > @duration
                @timeEnd = @duration
            if @timeStart >= @timeEnd
                @timeStart = 0.0
            @updateBar()

            for sub in @subtitles
                elm.target.appendChild(sub.node)
            return
        ).bind(@)
        @video.load()
        @audioSwitchingInProgress = false
        @LI = 0
        @RI = 1
        @SI = undefined
        $('#' + @audio_inter[@LI]['html-id']).addClass 'left'
        $('#' + @audio_inter[@RI]['html-id']).addClass 'right'
        @timeline_pb = document.getElementById('timeline-pb')
        @timeline_back = document.getElementById('timeline-back')
        @bars = []
        # Program in/out data to use Timeline.update()

        @id = 'program-selection-bar'
        @doc_currentTime = document.getElementById('current-time')
        @doc_audioDelay = document.getElementById('audio-delay')
        @doc_audioSync1 = document.getElementById('audio-sync1')
        @doc_audioSync2 = document.getElementById('audio-sync2')
        @doc_barSync1 = document.getElementById('bar-sync1')
        @doc_barSync2 = document.getElementById('bar-sync2')
        @timeBend = 1.0
        @timeOffset = 0.0
        @updateDelay()
        @update_counter = 10
        @sync_counter = 2
        @updateInterval = setInterval((->
            @updateTime()
            return
        ).bind(this), 40)
        @timeline_back.addEventListener 'click', @seek.bind(this), false
        return

    play: ->
        console.log('player.play()')
        @video.play()
        @audio_inter[@LI].node.connect @interaction_channelMerger, 0, 0
        @audio_inter[@RI].node.connect @interaction_channelMerger, 0, 1
        @audio_inter[@LI].audio.play()
        @audio_inter[@RI].audio.play()
        @audio_inter[@RI].audio.currentTime = @audio_inter[@LI].audio.currentTime
        return

    pause: ->
        @video.pause()
        @audio_inter[@LI].audio.pause()
        @audio_inter[@RI].audio.pause()
        return

    stop: ->
        clearInterval @updateInterval
        $(@timeline_back).unbind 'click'
        return

    # set IN time of current or new block
    # create new block only at blank right area

    setBlockIn: ->
        currentTime = @video.currentTime
        duration = @video.duration
        i = 0
        while i < @bars.length
            if @bars[i].timeStart >= currentTime or @bars[i].timeEnd >= currentTime
                @bars[i].setTimeStart currentTime
                return
            i++
        @bars.push new Timeline('sel_' + @bars.length, @video.duration)
        @bars[@bars.length - 1].setTimeStartEnd currentTime, duration
        return

    # set OUT time of current block

    setBlockOut: ->
        currentTime = @video.currentTime
        i = @bars.length
        while i > 0
            i--
            if @bars[i].timeStart < currentTime and @bars[i].timeEnd > currentTime
                @bars[i].setTimeEnd currentTime
                return
        return

    # Remove current block

    blockRemove: ->
        block = @_getCurrentBlock()
        if block
            block.remove()
            @bars.splice @bars.indexOf(block), 1
        return

    # set IN time of current or new block
    # create new block only at blank right area

    setProgramIn: ->
        currentTime = @video.currentTime
        duration = @video.duration
        @timeStart = currentTime
        if @timeEnd < currentTime
            @timeEnd = duration
        @updateBar()
        return

    # set OUT time of current block

    setProgramOut: ->
        currentTime = @video.currentTime
        @timeEnd = currentTime
        if @timeStart > currentTime
            @timeStart = 0.0
        @updateBar()
        return

    # Seek to start of program

    cueProgramIn: ->
        @_jumpToTime @timeStart
        return

    cueOffset: (offset) ->
        new_time = @audio_inter[@LI].audio.currentTime + offset
        if new_time < 0
            new_time = 0.0
        else if new_time > @duration
            new_time = duration
        @_jumpToTime new_time
        return

    # Seek to end of program

    cueProgramOut: ->
        @_jumpToTime @timeEnd
        return

    cueLeft: ->
        debugger
        time = @audio_inter[@LI].audio.currentTime
        # Collect all cues to array
        arr = [@timeStart, @timeEnd, @duration]
        aint = @audio_inter[@LI]
        if aint.sync1 != null
            arr.push(aint.sync1[0])
            if aint.sync2 != null
                arr.push(aint.sync2[0])
        arr = arr.sort((a, b) ->
            return a - b
        )
        pt = 0.0
        for t in arr
            if t + 0.1 - time > 0
                time = pt
                break
            pt = t
        @_jumpToTime time
        return

    cueRight: ->
        debugger
        time = @audio_inter[@LI].audio.currentTime
        # Collect all cues to array
        arr = [@timeEnd, @timeStart, 0.0]
        aint = @audio_inter[@LI]
        if aint.sync1 != null
            arr.push(aint.sync1[0])
            if aint.sync2 != null
                arr.push(aint.sync2[0])
        arr = arr.sort((a, b) ->
            return b - a
        )
        pt = @duration
        for t in arr
            if time + 0.1 - t > 0
                time = pt
                break
            pt = t
        @_jumpToTime time
        return

    # Seek to start of current block

    cueBlockIn: ->
        block = @_getCurrentBlock()
        if block
            @_jumpToTime block.timeStart
        return

    # Seek to end of current block

    cueBlockOut: ->
        block = @_getCurrentBlock()
        if block
            @_jumpToTime block.timeEnd
        return

    selectChannel: (channel) ->
        playing = !@video.paused
        if playing
            @video.pause()
            @audio_inter[@LI].audio.pause()
            @audio_inter[@RI].audio.pause()
            @audio_inter[@LI].node.disconnect()
            @audio_inter[@RI].node.disconnect()
        # Remove L/R classes, add cXX back
        $('#' + @audio_inter[@LI]['html-id']).removeClass 'left'
        $('#' + @audio_inter[@RI]['html-id']).removeClass 'right'
        @audioSwitchingInProgress = true
        @LI = channel
        @RI = (channel + 1) % @audio_inter.length
        @updateDelay()
        delay = @audio_inter[@LI].delay_ms / 1000.0
        @audio_inter[@LI].node.connect @interaction_channelMerger, 0, 0
        @audio_inter[@RI].node.connect @interaction_channelMerger, 0, 1
        if playing
            @video.play()
            @audio_inter[@LI].audio.play()
            @audio_inter[@RI].audio.play()
            @audio_inter[@LI].audio.currentTime = @video.currentTime - delay
            @audio_inter[@RI].audio.currentTime = @video.currentTime - delay
        $('#' + @audio_inter[@LI]['html-id']).addClass 'left'
        $('#' + @audio_inter[@RI]['html-id']).addClass 'right'
        return

    _deactivateProSubAdd: ->
        $('#pro-sub-add').removeClass('clickable')
        $('#pro-sub-add').unbind 'click'
        return

    _activateProSubAdd: ->
        $('#pro-sub-add').bind('click', (->
            # Add audio layout to output
            console.log('====================\npro-sub-add')
            lang = document.getElementById('pro-audio-lang').value
            layout = document.getElementById('pro-audio-layout-select').value
            cl = []
            i = 0
            for pos, idx in AudioMan.audioLayouts[layout].layout
                id = 'map' + idx + '-' + pos + '-select'
                console.log(id)
                sel = document.getElementById(id).value
                console.log(sel)
                cl.push sel
                i++
            console.log(cl)
            console.log('====================')
            @interaction_internal.addAudioOutput(lang, AudioMan.audioLayouts[layout].code, cl)
            return
        ).bind(@))
        $('#pro-sub-add').addClass('clickable')
        return

    selectSubtitles: (si) ->
        # TODO: auto-select source language code
        if @SI != undefined
            @subtitles[@SI].node.mode = 'hidden'
            @video.textTracks[@SI].mode = 'hidden'
            $('#' + @subtitles[@SI]['html-id']).removeClass 'activesubs'
        if @SI == si
            @SI = undefined
            @_deactivateProSubAdd()
        else
            @SI = si
            @subtitles[@SI].node.mode = 'showing'
            @video.textTracks[@SI].mode = 'showing'
            $('#' + @subtitles[@SI]['html-id']).addClass 'activesubs'
            @_activateProSubAdd()
        return

    seek: (e) ->
        playing = !@video.paused
        if playing
            @video.pause()
            @audio_inter[@LI].audio.pause()
            @audio_inter[@RI].audio.pause()
        seekTimeV = e.layerX / $(@timeline_back).width() * @video.duration
        seekTimeA = seekTimeV - (@audio_inter[@LI].delay_ms / 1000.0)
        @_setCurrentTime seekTimeV, seekTimeA
        if playing
            @video.play()
            @audio_inter[@LI].audio.play()
            @audio_inter[@RI].audio.play()
        return

    _sync_str: (sync, elm) ->
        if sync == null or sync == undefined
            elm.style.display = 'none'
            return 'No sync point'
        elm.style.left = (100.0 * sync[0]/@duration) + '%'
        elm.style.display = 'block'
        return Timecode.timecode(sync[0])+' ('+sync[1].toFixed(2)+')'

    updateDelay: ->
        @doc_audioDelay.innerHTML = @audio_inter[@LI].delay_ms + 'ms'
        @doc_audioSync1.innerHTML = @_sync_str(@audio_inter[@LI].sync1, @doc_barSync1)
        @doc_audioSync2.innerHTML = @_sync_str(@audio_inter[@LI].sync2, @doc_barSync2)
        return

    decreaseDelay: ->
        @audio_inter[@LI].delay_ms -= 50
        @doc_audioDelay.innerHTML = @audio_inter[@LI].delay_ms + 'ms'
        return

    increaseDelay: ->
        @audio_inter[@LI].delay_ms += 50
        @doc_audioDelay.innerHTML = @audio_inter[@LI].delay_ms + 'ms'
        return

    addSyncPoint: ->
        aint = @audio_inter[@LI]
        audioCurrentTime = aint.audio.currentTime
        delay = 0.001 * aint.delay_ms
        if aint.sync1 == null or audioCurrentTime <= aint.sync1[0]
            aint.sync1 = [audioCurrentTime, delay]
            aint.sync2 = null
        else
            aint.sync2 = [audioCurrentTime, delay]
            ta1 = aint.sync1[0]
            ta2 = aint.sync2[0]
            tv1 = ta1 + aint.sync1[1]
            tv2 = ta2 + aint.sync2[1]
            @timeBend = (tv2 - tv1) / (ta2 - ta1)
            @timeOffset = tv1 - @timeBend*ta1
        # Calculate program in/out
        @updateDelay()

    synchronize: ->
        if @audioSwitchingInProgress
            @audioSwitchingInProgress = false
            return
        videoCurrentTime = @video.currentTime
        audioCurrentTime = @audio_inter[@LI].audio.currentTime
        if @audio_inter[@LI].sync2 == null
            videoCalcTime = audioCurrentTime + (@audio_inter[@LI].delay_ms / 1000.0)
        else
            videoCalcTime = @timeOffset + @timeBend*audioCurrentTime
        delta = videoCurrentTime - videoCalcTime
        @sync_counter = 4
        if @video.readyState > 0 and Math.abs(delta) > 0.05
            @video.currentTime = videoCalcTime
            @sync_counter = 20
        return

    updateTime: ->
        @update_counter -= 1
        if @update_counter < 1
            vct = @video.currentTime
            delay_ms = parseInt(1000.0 * (vct - @audio_inter[@LI].audio.currentTime))
            @doc_currentTime.innerHTML = Timecode.timecode(vct)
            #+ ' (' + delay_ms + 'ms)'
            @timeline_pb.style.width = 100 * @video.currentTime / @video.duration + '%'
            @update_counter = 3
        @sync_counter -= 1
        if @sync_counter < 1
            @synchronize()
        return

    updateBar: ->
        x = 100 * @timeStart / @duration
        w = 100 * (@timeEnd - (@timeStart)) / @duration
        el = document.getElementById(@id)
        el.style.left = x + '%'
        el.style.width = w + '%'
        return

    _jumpToTime: (time) ->
        seekTimeV = time
        seekTimeA = seekTimeV - (@audio_inter[@LI].delay_ms / 1000.0)
        @_setCurrentTime seekTimeV, seekTimeA
        return

    _setCurrentTime: (seekTimeV, seekTimeA) ->
        @video.currentTime = seekTimeV
        @audio_inter[@LI].audio.currentTime = seekTimeA
        @audio_inter[@RI].audio.currentTime = seekTimeA
        return

    _getCurrentBlock: ->
        currentTime = @video.currentTime
        i = @bars.length
        j = -1
        # Find matched bar
        while i > 0
            i--
            if @bars[i].timeStart <= currentTime and @bars[i].timeEnd >= currentTime
                j = i
                break
        @bars[j]

    get_audio_element: (idx) ->
        @audio_inter[idx]

    get_audio_element_current: () ->
        @audio_inter[@LI]

module.exports = InteractionPlayer

