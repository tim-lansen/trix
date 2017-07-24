(function(){
    var simpleStringDistance = function(s, t) {
        s = s.toLowerCase();
        t = t.toLowerCase();
        if (s === t)
            return 0;
        var dist = 1, d = 1024;
        for (var i = 0; d > 1 && s.length > i && t.length > i; i++, d >>= 1) {
            if (s[i] !== t[i])
                dist += d;
        }
        return dist;
    };

    module.exports = simpleStringDistance;
})();
