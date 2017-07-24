(function(document){
    "use strict";

    const $ = require('jquery');

    class Interaction {
        constructor (data, player) {
            this.id = data.id;
            this.data_in = data.data;
            this.ctime = data.ctime;
            this.changed = false;
            this.data_out = {'id': data.id, 'movie': data.movie, 'studio': data.studio};
            this.player = player;
            if (data.audio_map) {
                this.data_out.audio_map = data.audio_map;
            }
        }

        audioRemoveUnbindAll () {
            if (!('audio_map' in this.data_out)) {
                return;
            }
            if (this.data_out.audio_map.length === 0) {
                return;
            }
            for (var i in this.data_out.audio_map) {
                $('#audio-out-remove-'+zpad(i,2)).unbind();
            }
        }

        audioRemoveBindAll () {
            if (!('audio_map' in this.data_out)) {
                return;
            }
            if (this.data_out.audio_map.length === 0) {
                return;
            }
            var int = this;
            function removeAudioOutput(i){
                return function(){
                    return int.removeAudioOutput(Number(i));
                };
            }
            for (let i in this.data_out.audio_map) {
                $('#audio-out-remove-'+zpad(i,2)).bind('click', removeAudioOutput(i));
            }
        }

        addAudioOutput (language, layout_code, channel_map) {
            this.audioRemoveUnbindAll();
            if (!('audio_map' in this.data_out)) {
                this.data_out.audio_map = [];
            }
            this.data_out.audio_map.push({
                'lang': language,
                'layout': layout_code,
                'map': channel_map,
                'delay': this.player.audio_inter[this.player.LI].delay_ms/1000.0
            });
            this.showAudioOutputs();
            this.audioRemoveBindAll();
        }

        removeAudioOutput (index) {
            console.log('remove audio '+index);
            this.audioRemoveUnbindAll();
            if (!('audio_map' in this.data_out)) {
                return;
            }
            if (index >= this.data_out.audio_map.length) {
                return;
            }
            this.data_out.audio_map.splice(index, 1);
            this.showAudioOutputs();
            this.audioRemoveBindAll();
        }

        showAudioOutputs () {
            // Rebuild audio destination table
            var html = '';
            var amap;
            if (this.data_out.audio_map) {
                for (var i in this.data_out.audio_map) {
                    //{'lang': 'rus', 'layout': '5.1', 'delay': 1.0, 'map': [0, 1, 2, 3, 4, 5]},
                    amap = this.data_out.audio_map[i];
                    html += '<tr class="audio-out row' + i%2 + '">';
                    html +=   '<td class="audio-out col0">' + amap.lang + '</td>';
                    html +=   '<td class="audio-out col1">';
                    html +=     '<div style="position: relative; top: 0; left: 0; z-index: 1;">';
                    html +=       '<span>' + amap.layout + ' [' + amap.map + ']</span>';
                    html +=       '<span id="audio-out-remove-'+zpad(i,2)+'" class="audio-out-btnDelete">&times;</span>';
                    html +=     '</div>';
                    html +=   '</td>';
                    html += '</tr>';
                }
            }
            document.getElementById('audio-out-table').innerHTML = html;
        }

        showMovie () {
            document.getElementById('dst-movie-title').innerHTML = this.data_out.movie;
            document.getElementById('dst-movie-studio').innerHTML = this.data_out.studio;
        }
    }
    module.exports = Interaction;
})(document);