#'use strict'
$ = require('jquery')

class InteractionInternal
    constructor: (asset, audio_channels_map, player) ->
        @asset = asset
        @changed = false
#            'id': data.id
#            'movie': data.movie
#            'studio': data.studio
        @player = player
        @audio_channels_map = audio_channels_map
        console.log(audio_channels_map)
        return

    update_asset: (livecrop) ->
        if @asset != null and @player != null
            vs = @asset.videoStreams[0]
            vs.program_in = @player.timeStart
            vs.program_out = @player.timeEnd
            livecrop.updateCropDetect(vs.cropdetect)


    audioRemoveUnbindAll: ->
        for stream, i in @asset.audioStreams
            rmid = 'audio-out-remove-' + zpad(i, 2)
            $('#' + rmid).unbind()
        return

    audioRemoveBindAll: ->
        rao = (i) ->
            ->
                int.removeAudioOutput(Number(i))

        int = @
        for stream, i in @asset.audioStreams
            rmid = 'audio-out-remove-' + zpad(i, 2)
            $('#' + rmid).bind('click', rao(i))
        return

    addAudioOutput: (language, layout_code, channel_map) ->
        @audioRemoveUnbindAll()
        stream = new Asset_AudioStream()
        stream.type = 1 # audio
        stream.layout = layout_code  # None
        stream.channels = []
        stream.language = language
        stream.program_in = null  # None
        stream.program_out = null  # None

        for ai in channel_map
            stream.channels.push({'src_stream_index': @audio_channels_map[ai][0], 'src_channel_index': @audio_channels_map[ai][1]})
        console.log(stream.channels)
        # TODO: calc program_in, program_out
        stream.delay = @player.audio_inter[@player.LI].delay_ms / 1000.0

        @asset.audioStreams.push(stream)

        console.log(@player.get_audio_element_current())
        console.log(channel_map)
        console.log(stream)

        @showAudioOutputs()
        @audioRemoveBindAll()
        return

    removeAudioOutput: (index) ->
        console.log 'remove audio ' + index
        @audioRemoveUnbindAll()
        @asset.audioStreams.splice(index, 1)
        @showAudioOutputs()
        @audioRemoveBindAll()
        return

    showAudioOutputs: ->
        # Rebuild audio destination table
        html = ''
        for stream, i in @asset.audioStreams
            rmid = 'audio-out-remove-' + zpad(i, 2)
            html += '<tr class="audio-out row' + i % 2 + '">'
            html += '<td class="audio-out col0">' + stream.language + '</td>'
            html += '<td class="audio-out col1">'
            html += '<div style="position:relative;top:0;left:0;z-index:1;">'
            html += '<span id="' + rmid + '">' + stream.layout + '</span>'
            html += '<span class="audio-out-btnDelete">&times;</span>'
            html += '</div>'
            html += '</td>'
            html += '</tr>'
        document.getElementById('audio-out-table').innerHTML = html
        return

    showMovie: ->
        document.getElementById('dst-content-title').innerHTML = @asset.name
        document.getElementById('dst-content-id').innerHTML = @asset.programId
        return
