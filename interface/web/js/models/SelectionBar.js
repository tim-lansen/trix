(function(document){
    "use strict";

    class SelectionBar {
        constructor (id, duration) {
            if(id === null) {
                throw new Exception('id argument is mandatory');
            }
            if(duration === null) {
                throw new Exception('duration argument is mandatory');
            }
            this.duration = duration;
            this.id       = id;
            this._render();
        }

        setTimeStartEnd (timeStart, timeEnd) {
            this.timeStart = timeStart;
            this.timeEnd   = timeEnd;
            this.updateBar();
        }

        setTimeStart (timeStart) {
            this.timeStart = timeStart;
            this.updateBar();
        }

        setTimeEnd (timeEnd) {
            this.timeEnd = timeEnd;
            this.updateBar();
        }

        remove () {
            if(this.el){
                this.el.parentNode.removeChild(this.el);
            }
        }

        updateId (id) {
            this.id = id;
            this._render();
            this.updateBar();
        }

        updateBar () {
            let x = 100 * (this.timeStart/this.duration);
            let w = 100 * ((this.timeEnd - this.timeStart)/this.duration);
            this.el.style.left  = x + '%';
            this.el.style.width = w + '%';
        }

        _template (data) {
            return '<div id="' + data.id + '" class="' + data.className+ '"></div>';
        }

        _render () {
            if(!this.parentElement){
                this.parentElement = document.querySelector(this.parentSelector);
            }
            let node = document.createElement('div');
            node.innerHTML = this._template(this);
            this.parentElement.appendChild(node.firstChild);
            this.el = document.getElementById(this.id);
        }
    }

    SelectionBar.prototype.className = 'sample-selection-bar';
    SelectionBar.prototype.parentSelector = '#selection-bar-back';

    module.exports = SelectionBar;
})(document);