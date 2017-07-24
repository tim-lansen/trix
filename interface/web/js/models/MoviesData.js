(function(document){
    "use strict";

    const $         = require('jquery');
    const x2js      = require('x2js');
    //const filters   = require('../lib/Filters');
    const getDef    = require('../lib/getDef');
    const saveFile  = require('../lib/saveFile');
    const copyTextToClipboard = require('../lib/copyTextToClipboard');
    const xml2js = new x2js();
    const iso639ru = require('../lib/iso639_ruRU.json');
    const iso639en = require('../lib/iso639_enUS.json');

    class MoviesData {
        constructor (app) {
            // TODO: make 'filters' an argument
            // this.parent = parent;
            this.app = app;
            this.rightholders = app.shared.rightholders;
            // this.filters = parent.filters;
            this.id_movies = {};
            // this.api_movies = [];
            this.selectedMovieIndex = undefined;
            this.update_id = null;
        }

        refresh (callback) {
            const wsNapi = this.app.shared.wsNapi;
            this.app.setMainStatus('Requesting list of movies...');
            this.app.shared.update.movies_extra = [];
            wsNapi.request({
                    'method': 'movies_all',
                    'params': {}
                },
                function (m) {
                    const all_movies_ids = m.result.ids;//.slice(1,5);
                    // Continue requesting movies data
                    this.app.setMainStatus('Requesting movies data...');
                    wsNapi.request(
                        { method: 'movies_extra', params: { ids: all_movies_ids } },
                        function (m) {
                            console.log('Rebuild data...');
                            this.app.setMainStatus('Rebuild data...');
                            var r = m.result,
                                token = '',
                                i = 0,
                                j = 0;
                            for (i = 0; i < r.length; i++) {
                                r[i].rightholder = this.rightholders.api_rightholders[r[i].rightholder_ids[0]].name;
                                // Rebuild 'video' object
                                r[i].video_r = {};
                                for (const t in r[i].video) {
                                    for (j in r[i].video[t]) {
                                        if (!('type' in r[i].video[t][j]))
                                            r[i].video[t][j].type = 'null';
                                        token = t.replace('_files','')+'@'+
                                            r[i].video[t][j].type.replace('playready','pr').replace('offline','off')+'@'+
                                            r[i].video[t][j].streaming_type+'@'+r[i].video[t][j].quality;
                                        r[i].video_r[token] = r[i].video[t][j].url;
                                    }
                                }
                                // Rebuild 'audio' object
                                r[i].audio_r = {};
                                for (j in r[i].audio) {
                                    token = r[i].audio[j].lang+'@'+r[i].audio[j].layout;
                                    r[i].audio_r[token] = true;
                                }
                                r[i].subtitles_r = {};
                                for (j in r[i].subtitles) {
                                    token = r[i].subtitles[j].lang+'@';
                                    if (r[i].subtitles[j].forced)
                                        token += 'forced';
                                    r[i].subtitles_r[token] = true;
                                }
                                // Store record
                                this.id_movies[r[i].id] = r[i];
                            }
                            this.update_id = this.app.shared.UUID.generate();
                            console.log('Data has been rebuilt.');
                            if (typeof(callback) === 'function') {
                                callback();
                            }
                        }.bind(this)
                    );
                }.bind(this)
            );
        }


        getGuids () {
            var text = '';
            for (var i = 0; i < this.api_movies.length; i++) {
                // Check condition
                if (this.filters.checkCondition(this.api_movies[i], filterConditions[filterConditionIndex].condition))
                {
                    text += this.api_movies[i].id_guid + '\n';
                }
            }
            return text;
        }

        getIdsNames () {
            var text = '';
            for (var i = 0; i < this.api_movies.length; i++) {
                // Check condition
                if (this.filters.checkCondition(this.api_movies[i], filterConditions[filterConditionIndex].condition)) {
                    if (this.api_movies[i].hasOwnProperty('subtitles')) {
                        text += this.api_movies[i].id_guid;
                        for (var j = 0; j < this.api_movies[i].subtitles.length; j++) {
                            text += '\t' + this.api_movies[i].subtitles[j].url;
                        }
                        text += '\n';
                    }
                }
            }
            return text;
        }

        getUnstrictSlugs () {
            var text = '';
            var check = /^[a-z0-9-]+$/;
            for (var i = 0; i < this.api_movies.length; i++) {
                // Check slug
                var r = this.api_movies[i];
                if (!check.test(r.slug)) {
                    text += r.id + '\t' + r.slug + '\t' + r.rightholder + '\t' + r.original_title + '\n';
                }
            }
            return text;
        }

        checkMan (man_url) {
            // var man = e.target.parentNode.cells[1].innerText;
            console.log(man_url);

            $.ajax({
                url: man_url,
                method: "GET",
                dataType: "text"
            }).done(function(xmlData) {
                var audioTracks = [];
                var man = xml2js.xml2js(xmlData);

                if (!man.hasOwnProperty('SmoothStreamingMedia'))
                    return;
                if (!man.SmoothStreamingMedia.hasOwnProperty('StreamIndex'))
                    return;
                var i;
                for (i = 0; i < man.SmoothStreamingMedia.StreamIndex.length; i++) {
                    var sm = man.SmoothStreamingMedia.StreamIndex[i];
                    console.log(sm._Type + ': ' + sm._Language);
                    if (sm._Type === 'audio')
                        audioTracks.push(sm._Language);
                }
                var data = this.api_movies[this.selectedMovieIndex];
                if (!data.hasOwnProperty('audio')) {
                    document.getElementById('audio-consistant-info').innerHTML = 'Manifest has info about '+i+' audio track(s), but no audio track(s) registered. Click to fix.';
                    document.getElementById('audio-consistant-info').style.display = 'block';
                }
                else if (audioTracks.length !== data.audio.length) {
                    document.getElementById('audio-consistant-info').innerHTML = 'Manifest has info about '+audioTracks.length+' audio track(s), but '+data.audio.length+' audio track(s) registered. Click to fix.';
                    document.getElementById('audio-consistant-info').style.display = 'block';
                }
                else {
                    // Enumerate and compare parsed audio tracks and movie audio data
                    var equal = true;
                    for (i = 0; i < audioTracks.length; i++) {
                        var langP = audioTracks[i];
                        if(iso639en.alpha3to2mapping.hasOwnProperty(langP))
                            langP = iso639en.alpha3to2mapping[langP];
                        if (data.audio[i].lang !== langP) {
                            equal = false;
                            console.log('Track: '+i+' Parsed lang: '+langP+' Reg lang: '+data.audio[i].lang);
                        }
                    }
                    if (equal) {
                        document.getElementById('audio-consistant-info').innerHTML = 'Parsed list of audio tracks matches registered list.';
                        document.getElementById('audio-consistant-info').style.display = 'block';
                    } else {
                        document.getElementById('audio-consistant-info').innerHTML = 'Parsed list of audio tracks doesn\'t match registered list. Click to fix.';
                        document.getElementById('audio-consistant-info').style.display = 'block';
                    }
                }
                this.parsedAudioTracks = audioTracks;
            }.bind(this));
        }

        scanFixTracks () {
            $('#audio-consistant-info').unbind('click');
            $('#audio-consistant-info').bind('click', function () {
                var curlo = '';
                for (var ii = 0; ii < this.api_movies.length; ii++) {
                    if (typeof(this.api_movies[ii].curlo) !== "undefined")
                        curlo += this.api_movies[ii].curlo;
                }
                saveFile(curlo, 'curlout');
            }.bind(this));
            curlOut = '';
            for (var ii = 0; ii < this.api_movies.length; ii++) {
                var data = this.api_movies[ii];
                if (!data.hasOwnProperty('video'))
                    continue;
                if (!data.video.hasOwnProperty('movie_files'))
                    continue;
                for (var jj = 0; jj < data.video.movie_files.length; jj++) {
                    if (data.video.movie_files[jj].type === 'playready') {
                        var ldata = data;
                        var callback = function (d) {
                            var ldata = d;
                            var ljj = jj;
                            return function () {
                                console.log(ldata);
                                $.get(ldata.video.movie_files[ljj].url, function (xmlData) {
                                    var man = xml2js.xml2js(xmlData);
                                    // Quick solution
                                    // TODO: rewrite XML parser
                                    if (!man.hasOwnProperty('SmoothStreamingMedia')) {
                                        ldata.curlo = 'ID: '+ldata.id+' Problem: SmoothStreamingMedia\n';
                                        return;
                                    }
                                    if (!man.SmoothStreamingMedia.hasOwnProperty('StreamIndex')) {
                                        ldata.curlo = 'ID: '+ldata.id+' Problem: StreamIndex\n';
                                        return;
                                    }
                                    var curlo = '';
                                    var ai = 0;
                                    for (var i = 0; i < man.SmoothStreamingMedia.StreamIndex.length; i++) {
                                        var sm = man.SmoothStreamingMedia.StreamIndex[i];
                                        console.log(sm['@Type'] + ': ' + sm['@Language']);
                                        if (sm['@Type'] == 'audio') {
                                            curlo += 'curl -s -X POST --data \'{"method": "movie_audio_set", "params": {"movie_id": '+ldata.id+', "index": '+ai+', "lang": "'+ISO639.ISO_639_3_to_1[sm['@Language']]+'"}}\' --header \'X-USE-API: true\' --header \'X-GENERAL-INFO: {"device_token": "$device_token", "application": {"version": "4.0.1", "name": "web_admin"}, "device_info": {"serial_number": "vi deoengineer", "model": "engineer", "type": "internal", "name": "video"}, "version": "2", "last_event": null}\' http://ndrm.ayyo.ru/\n';
                                            ai += 1;
                                        }
                                    }
                                    ldata.curlo = curlo;
                                });
                            };
                        };
                        setTimeout(callback(data), ii*100);
                    }
                }
            }
        }

        buildProposedMovies (studio_rhId, movie) {
            // Build sorted list of proposed movies
            var titles = [];
            var ot;
            var otl;
            var guid;

            for (const id in this.api_movies[studio_rhId]) {
                ot = this.api_movies[studio_rhId][id].original_title;
                otl = this.api_movies[studio_rhId][id].original_title_legacy;
                guid = this.api_movies[studio_rhId][id].guid;
                titles.push([simpleStringDistance(otl, movie), studio_rhId, ot, id, guid, otl]);
            }
            titles.sort(function(a, b) {return a[0] - b[0];});
            // Build <select>
            var html = '';
            for (var i = 0; i < titles.length; i++) {
                html += '<option value="' + titles[i][3] + '">' + titles[i][2] + '</option>';
            }
            if (movie === titles[0][5])
                return {'select': html, 'title': titles[0][2]};
            return {'select': html};
        }
    }

    module.exports = MoviesData;
})(document);