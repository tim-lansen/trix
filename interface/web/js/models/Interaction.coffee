'use strict'
$ = require('jquery')

class Interaction
    constructor: (data, player) ->
        @id = data.id
        @data_in = data.data
        @ctime = data.ctime
        @changed = false
        @data_out =
            'id': data.id
            'movie': data.movie
            'studio': data.studio
        @player = player
        if data.audio_map
            @data_out.audio_map = data.audio_map
        return

    audioRemoveUnbindAll: ->
        if !('audio_map' of @data_out)
            return
        if @data_out.audio_map.length == 0
            return
        for i of @data_out.audio_map
            $('#audio-out-remove-' + zpad(i, 2)).unbind()
        return

    audioRemoveBindAll: ->

        removeAudioOutput = (i) ->
            ->
                int.removeAudioOutput Number(i)

        if !('audio_map' of @data_out)
            return
        if @data_out.audio_map.length == 0
            return
        int = this
        for i of @data_out.audio_map
            $('#audio-out-remove-' + zpad(i, 2)).bind 'click', removeAudioOutput(i)
        return

    addAudioOutput: (language, layout_code, channel_map) ->
        @audioRemoveUnbindAll()
        if !('audio_map' of @data_out)
            @data_out.audio_map = []
        @data_out.audio_map.push
            'lang': language
            'layout': layout_code
            'map': channel_map
            'delay': @player.audio_inter[@player.LI].delay_ms / 1000.0
        @showAudioOutputs()
        @audioRemoveBindAll()
        return

    removeAudioOutput: (index) ->
        console.log 'remove audio ' + index
        @audioRemoveUnbindAll()
        if !('audio_map' of @data_out)
            return
        if index >= @data_out.audio_map.length
            return
        @data_out.audio_map.splice index, 1
        @showAudioOutputs()
        @audioRemoveBindAll()
        return

    showAudioOutputs: ->
        # Rebuild audio destination table
        html = ''
        amap = undefined
        if @data_out.audio_map
            for i of @data_out.audio_map
                #{'lang': 'rus', 'layout': '5.1', 'delay': 1.0, 'map': [0, 1, 2, 3, 4, 5]},
                amap = @data_out.audio_map[i]
                html += '<tr class="audio-out row' + i % 2 + '">'
                html += '<td class="audio-out col0">' + amap.lang + '</td>'
                html += '<td class="audio-out col1">'
                html += '<div style="position: relative; top: 0; left: 0; z-index: 1;">'
                html += '<span>' + amap.layout + ' [' + amap.map + ']</span>'
                html += '<span id="audio-out-remove-' + zpad(i, 2) + '" class="audio-out-btnDelete">&times;</span>'
                html += '</div>'
                html += '</td>'
                html += '</tr>'
        document.getElementById('audio-out-table').innerHTML = html
        return

    showMovie: ->
        document.getElementById('dst-movie-title').innerHTML = @data_out.movie
        document.getElementById('dst-movie-studio').innerHTML = @data_out.studio
        return

module.exports = Interaction
