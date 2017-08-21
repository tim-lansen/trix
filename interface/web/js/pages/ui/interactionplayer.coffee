#'use strict'
#$ = require('jquery')
#Timeline = require('./Timeline')

class InteractionPlayer
    constructor: (video_object, video_elements, audio_elements, interaction_channelMerger) ->
        @video = video_object
        @audio_inter = audio_elements
        @interaction_channelMerger = interaction_channelMerger
        @video.appendChild video_elements[0]
        $(@video).one 'loadedmetadata', ((e) ->
            @timeEnd = e.currentTarget.duration
            @duration = e.currentTarget.duration
            return
        ).bind(@)
        @video.load()
        @audioSwitchingInProgress = false
        @LI = 0
        @RI = 1
        $('#' + @audio_inter[@LI]['html-id']).addClass 'left'
        $('#' + @audio_inter[@RI]['html-id']).addClass 'right'
        @timeline_pb = document.getElementById('timeline-pb')
        @timeline_back = document.getElementById('timeline-back')
        @bars = []
        # Program in/out data to use Timeline.update()
        @timeStart = 0.0
        @id = 'program-selection-bar'
        @doc_currentTime = document.getElementById('current-time')
        @doc_audioDelay = document.getElementById('audio-delay')
        @updateDelay()
        @update_counter = 10
        @sync_counter = 2
        @updateInterval = setInterval((->
            @updateTime()
            return
        ).bind(this), 50)
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

    # Seek to end of program

    cueProgramOut: ->
        @_jumpToTime @timeEnd
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

    updateDelay: ->
        @doc_audioDelay.innerHTML = @audio_inter[@LI].delay_ms + 'ms'
        return

    decreaseDelay: ->
        @audio_inter[@LI].delay_ms -= 50
        @doc_audioDelay.innerHTML = @audio_inter[@LI].delay_ms + 'ms'
        return

    increaseDelay: ->
        @audio_inter[@LI].delay_ms += 50
        @doc_audioDelay.innerHTML = @audio_inter[@LI].delay_ms + 'ms'
        return

    synchronize: ->
        if @audioSwitchingInProgress
            @audioSwitchingInProgress = false
            return
        currentTime = @video.currentTime
        audioCurrentTime = @audio_inter[@LI].audio.currentTime
        delta = currentTime - (@audio_inter[@LI].delay_ms / 1000.0) - audioCurrentTime
        @sync_counter = 2
        if @video.readyState > 0 and Math.abs(delta) > 0.05
            @video.controller.currentTime = audioCurrentTime + @audio_inter[@LI].delay_ms / 1000.0
            @sync_counter = 20
        return

    updateTime: ->
        @update_counter -= 1
        if @update_counter < 1
            @doc_currentTime.innerHTML = @video.currentTime.toFixed(2)
            @timeline_pb.style.width = 100 * @video.currentTime / @video.duration + '%'
            @update_counter = 10
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

module.exports = InteractionPlayer

