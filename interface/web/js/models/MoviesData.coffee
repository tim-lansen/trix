'use strict'
$ = require('jquery')
x2js = require('x2js')
#const filters   = require('../lib/Filters');
getDef = require('../lib/getDef')
saveFile = require('../lib/saveFile')
copyTextToClipboard = require('../lib/copyTextToClipboard')
xml2js = new x2js
iso639ru = require('../lib/iso639_ruRU.json')
iso639en = require('../lib/iso639_enUS.json')

class MoviesData
    # TODO: make 'filters' an argument
    # this.parent = parent;
    constructor: (app) ->
        @app = app
        @rightholders = app.shared.rightholders
        # this.filters = parent.filters;
        @id_movies = {}
        # this.api_movies = [];
        @selectedMovieIndex = undefined
        @update_id = null
        return

    refresh: (callback) ->
        @app.setMainStatus 'Requesting list of movies...'
        @app.shared.update.movies_extra = []
        @app.shared.wsNapi.request {
            'method': 'movies_all'
            'params': {}
        }, ((msg) ->
            MoviesData.callback obj, msg, callback
        )
        return

    @method_handlers:
        movies_all: MoviesData.handle_movies_all
        movies_extra: MoviesData.handle_movies_extra

    @callback: (obj, message) ->
        try
            MoviesData.method_handlers[message.method] obj, message.result
        catch error
            console.log error
        return

    @handle_movies_all: (obj, result, callback) ->
        try
            obj.all_movies_ids = result.ids
            obj.app.setMainStatus 'Requesting movies data...'
            obj.app.shared.wsNapi.request {
                'method': 'movies_extra'
                'params': {}
            }, ((msg) ->
                MoviesData.callback obj, msg, callback
            )
        catch error
            console.log error
        return

    @handle_movies_extra: (obj, result, callback) ->
        try
            obj.rebuild_data result
            if typeof callback == 'function'
                callback()
            return
        catch error
            console.log error
        return

    rebuild_data: (result) ->
        console.log 'Rebuild data...'
        @app.setMainStatus 'Rebuild data...'
        r = result
        token = ''
        i = 0
        j = 0
        i = 0
        while i < r.length
            r[i].rightholder = @rightholders.api_rightholders[r[i].rightholder_ids[0]].name
            # Rebuild 'video' object
            r[i].video_r = {}
            for t of r[i].video
                for j of r[i].video[t]
                    `j = j`
                    if !('type' of r[i].video[t][j])
                        r[i].video[t][j].type = 'null'
                    token = t.replace('_files', '') + '@' + r[i].video[t][j].type.replace('playready', 'pr').replace('offline', 'off') + '@' + r[i].video[t][j].streaming_type + '@' + r[i].video[t][j].quality
                    r[i].video_r[token] = r[i].video[t][j].url
            # Rebuild 'audio' object
            r[i].audio_r = {}
            for j of r[i].audio
                `j = j`
                token = r[i].audio[j].lang + '@' + r[i].audio[j].layout
                r[i].audio_r[token] = true
            r[i].subtitles_r = {}
            for j of r[i].subtitles
                `j = j`
                token = r[i].subtitles[j].lang + '@'
                if r[i].subtitles[j].forced
                    token += 'forced'
                r[i].subtitles_r[token] = true
            # Store record
            @id_movies[r[i].id] = r[i]
            i++
        @update_id = @app.shared.UUID.generate()
        console.log 'Data has been rebuilt.'
        return


    getGuids: ->
        text = ''
        i = 0
        while i < @api_movies.length
            # Check condition
            if @filters.checkCondition(@api_movies[i], filterConditions[filterConditionIndex].condition)
                text += @api_movies[i].id_guid + '\n'
            i++
        text

    getIdsNames: ->
        text = ''
        i = 0
        while i < @api_movies.length
            # Check condition
            if @filters.checkCondition(@api_movies[i], filterConditions[filterConditionIndex].condition)
                if @api_movies[i].hasOwnProperty('subtitles')
                    text += @api_movies[i].id_guid
                    j = 0
                    while j < @api_movies[i].subtitles.length
                        text += '\u0009' + @api_movies[i].subtitles[j].url
                        j++
                    text += '\n'
            i++
        text

    getUnstrictSlugs: ->
        text = ''
        check = /^[a-z0-9-]+$/
        i = 0
        while i < @api_movies.length
            # Check slug
            r = @api_movies[i]
            if !check.test(r.slug)
                text += r.id + '\u0009' + r.slug + '\u0009' + r.rightholder + '\u0009' + r.original_title + '\n'
            i++
        text

    checkMan: (man_url) ->
        # var man = e.target.parentNode.cells[1].innerText;
        console.log man_url
        $.ajax(
            url: man_url
            method: 'GET'
            dataType: 'text').done ((xmlData) ->
            audioTracks = []
            man = xml2js.xml2js(xmlData)
            if !man.hasOwnProperty('SmoothStreamingMedia')
                return
            if !man.SmoothStreamingMedia.hasOwnProperty('StreamIndex')
                return
            i = undefined
            i = 0
            while i < man.SmoothStreamingMedia.StreamIndex.length
                sm = man.SmoothStreamingMedia.StreamIndex[i]
                console.log sm._Type + ': ' + sm._Language
                if sm._Type == 'audio'
                    audioTracks.push sm._Language
                i++
            data = @api_movies[@selectedMovieIndex]
            if !data.hasOwnProperty('audio')
                document.getElementById('audio-consistant-info').innerHTML = 'Manifest has info about ' + i + ' audio track(s), but no audio track(s) registered. Click to fix.'
                document.getElementById('audio-consistant-info').style.display = 'block'
            else if audioTracks.length != data.audio.length
                document.getElementById('audio-consistant-info').innerHTML = 'Manifest has info about ' + audioTracks.length + ' audio track(s), but ' + data.audio.length + ' audio track(s) registered. Click to fix.'
                document.getElementById('audio-consistant-info').style.display = 'block'
            else
                # Enumerate and compare parsed audio tracks and movie audio data
                equal = true
                i = 0
                while i < audioTracks.length
                    langP = audioTracks[i]
                    if iso639en.alpha3to2mapping.hasOwnProperty(langP)
                        langP = iso639en.alpha3to2mapping[langP]
                    if data.audio[i].lang != langP
                        equal = false
                        console.log 'Track: ' + i + ' Parsed lang: ' + langP + ' Reg lang: ' + data.audio[i].lang
                    i++
                if equal
                    document.getElementById('audio-consistant-info').innerHTML = 'Parsed list of audio tracks matches registered list.'
                    document.getElementById('audio-consistant-info').style.display = 'block'
                else
                    document.getElementById('audio-consistant-info').innerHTML = 'Parsed list of audio tracks doesn\'t match registered list. Click to fix.'
                    document.getElementById('audio-consistant-info').style.display = 'block'
            @parsedAudioTracks = audioTracks
            return
        ).bind(this)
        return

    scanFixTracks: ->
        $('#audio-consistant-info').unbind 'click'
        $('#audio-consistant-info').bind 'click', (->
            curlo = ''
            ii = 0
            while ii < @api_movies.length
                if typeof @api_movies[ii].curlo != 'undefined'
                    curlo += @api_movies[ii].curlo
                ii++
            saveFile curlo, 'curlout'
            return
        ).bind(this)
        ii = 0
        while ii < @api_movies.length
            data = @api_movies[ii]
            if !data.hasOwnProperty('video')
                ii++
                continue
            if !data.video.hasOwnProperty('movie_files')
                ii++
                continue
            jj = 0
            while jj < data.video.movie_files.length
                if data.video.movie_files[jj].type == 'playready'
                    ldata = data

                    callback = (d) ->
                        `var ldata`
                        ldata = d
                        ljj = jj
                        ->
                            console.log ldata
                            $.get ldata.video.movie_files[ljj].url, (xmlData) ->
                                man = xml2js.xml2js(xmlData)
                                # Quick solution
                                # TODO: rewrite XML parser
                                if !man.hasOwnProperty('SmoothStreamingMedia')
                                    ldata.curlo = 'ID: ' + ldata.id + ' Problem: SmoothStreamingMedia\n'
                                    return
                                if !man.SmoothStreamingMedia.hasOwnProperty('StreamIndex')
                                    ldata.curlo = 'ID: ' + ldata.id + ' Problem: StreamIndex\n'
                                    return
                                curlo = ''
                                ai = 0
                                i = 0
                                while i < man.SmoothStreamingMedia.StreamIndex.length
                                    sm = man.SmoothStreamingMedia.StreamIndex[i]
                                    console.log sm['@Type'] + ': ' + sm['@Language']
                                    if sm['@Type'] == 'audio'
                                        curlo += 'curl -s -X POST --data \'{"method": "movie_audio_set", "params": {"movie_id": ' + ldata.id + ', "index": ' + ai + ', "lang": "' + ISO639.ISO_639_3_to_1[sm['@Language']] + '"}}\' --header \'X-USE-API: true\' --header \'X-GENERAL-INFO: {"device_token": "$device_token", "application": {"version": "4.0.1", "name": "web_admin"}, "device_info": {"serial_number": "vi deoengineer", "model": "engineer", "type": "internal", "name": "video"}, "version": "2", "last_event": null}\' http://ndrm.ayyo.ru/\n'
                                        ai += 1
                                    i++
                                ldata.curlo = curlo
                                return
                            return

                    setTimeout callback(data), ii * 100
                jj++
            ii++
        return

    buildProposedMovies: (studio_rhId, movie) ->
    # Build sorted list of proposed movies
        titles = []
        ot = undefined
        otl = undefined
        guid = undefined
        for id of @api_movies[studio_rhId]
            ot = @api_movies[studio_rhId][id].original_title
            otl = @api_movies[studio_rhId][id].original_title_legacy
            guid = @api_movies[studio_rhId][id].guid
            titles.push [
                simpleStringDistance(otl, movie)
                studio_rhId
                ot
                id
                guid
                otl
            ]
        titles.sort (a, b) ->
            a[0] - (b[0])
        # Build <select>
        html = ''
        i = 0
        while i < titles.length
            html += '<option value="' + titles[i][3] + '">' + titles[i][2] + '</option>'
            i++
        if movie == titles[0][5]
            return {
                'select': html
                'title': titles[0][2]
            }
        { 'select': html }

module.exports = MoviesData

