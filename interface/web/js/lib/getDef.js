// Get definition from video URL
(function(document, window){
    var console = window.console;

    var defQueue = [];
    var definitions = {};
    var getDefActive = false;
    var video_object = document.createElement('video');
    video_object.addEventListener('loadeddata', function (e) { getDef(e); video_object.innerHTML = ''; }, false);
    video_object.addEventListener('error', function (e) { console.log('Error'); getDef(); }, false);

    function getDef (e) {
        if (typeof(e) !== 'undefined') {
            console.log(defQueue.length);
            var a = e.path[0].currentSrc;
            if (e.path[0].videoWidth >= 1280 || e.path[0].videoHeight >= 720) {
                definitions[a] = 'HD';
            } else {
                definitions[a] = 'SD';
            }

            if (!defQueue.length) {
                getDefActive = false;
            }
        }

        if (defQueue.length > 0) {
            getDefActive = true;
            const a = defQueue.shift();
            var video_src = document.createElement('source');
            video_src.type = 'video/mp4';
            video_src.src = a;
            video_object.appendChild(video_src);
            video_object.load();
        }
    }

    module.exports = getDef;
})(document, window);
