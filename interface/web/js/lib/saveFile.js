(function(window, document){
    var saveFile = function () {
        var a = document.createElement('a');
        document.body.appendChild(a);
        a.style = "display: none";
        return function (text, fileName) {
            var blob = new Blob([text], {type: "text/csv"});
            var url = window.URL.createObjectURL(blob);
            a.href = url;
            a.download = fileName;
            a.click();
            window.URL.revokeObjectURL(url);
        };
    };

    module.exports = saveFile;
})(window, document);
