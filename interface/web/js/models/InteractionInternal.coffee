#'use strict'
$ = require('jquery')

class InteractionInternal
    constructor: (asset, audio_channels_map, player) ->
#        @id = data.id
        @assetIn = asset
        @changed = false
        @assetOut = JSON.parse(JSON.stringify(asset))
#            'id': data.id
#            'movie': data.movie
#            'studio': data.studio
        @player = player
        @audio_channels_map = audio_channels_map
        console.log(audio_channels_map)
        return

    audioRemoveUnbindAll: ->
        for stream, i in @assetOut.audioStreams
            rmid = 'audio-out-remove-' + zpad(i, 2)
            $(rmid).unbind()
        return

    audioRemoveBindAll: ->
        int = @
        for stream, i in @assetOut.audioStreams
            rmid = 'audio-out-remove-' + zpad(i, 2)
            $(rmid).bind('click',  ->
                return int.removeAudioOutput(Number(i))
            )
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

        @assetOut.audioStreams.push(stream)

#        @data_out.audio_map.push
#            'lang': language
#            'layout': layout_code
#            'map': channel_map
#            'delay': @player.audio_inter[@player.LI].delay_ms / 1000.0
        @showAudioOutputs()
        @audioRemoveBindAll()
        return

    removeAudioOutput: (index) ->
        console.log 'remove audio ' + index
        @audioRemoveUnbindAll()
        @assetOut.audioStreams.splice(index, 1)
        @showAudioOutputs()
        @audioRemoveBindAll()
        return

    showAudioOutputs: ->
        # Rebuild audio destination table
        html = ''
        for stream, i in @assetOut.audioStreams
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
#        document.getElementById('dst-movie-title').innerHTML = @data_out.movie
#        document.getElementById('dst-movie-studio').innerHTML = @data_out.studio
        document.getElementById('dst-movie-title').innerHTML = 'TODO InteractionInternal::showMovie'
        document.getElementById('dst-movie-studio').innerHTML = 'TODO InteractionInternal::showMovie'
        return

#module.exports = InteractionInternal
