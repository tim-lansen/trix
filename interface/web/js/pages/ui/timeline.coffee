
class Timeline

    @className = 'sample-selection-bar'
    @parentSelector = '#selection-bar-back'

    constructor: (id, duration) ->
        if id == null
            throw new Exception('id argument is mandatory')
        if duration == null
            throw new Exception('duration argument is mandatory')
        @duration = duration
        @id = id
        @_render()
        return

    setTimeStartEnd: (timeStart, timeEnd) ->
        @timeStart = timeStart
        @timeEnd = timeEnd
        @updateBar()
        return

    setTimeStart: (timeStart) ->
        @timeStart = timeStart
        @updateBar()
        return

    setTimeEnd: (timeEnd) ->
        @timeEnd = timeEnd
        @updateBar()
        return

    remove: ->
        if @el
            @el.parentNode.removeChild @el
        return

    updateId: (id) ->
        @id = id
        @_render()
        @updateBar()
        return

    updateBar: ->
        x = 100 * @timeStart / @duration
        w = 100 * (@timeEnd - (@timeStart)) / @duration
        @el.style.left = x + '%'
        @el.style.width = w + '%'
        return

    _template: (data) ->
        '<div id="' + data.id + '" class="' + data.className + '"></div>'

    _render: ->
        if !@parentElement
            @parentElement = document.querySelector(@parentSelector)
        node = document.createElement('div')
        node.innerHTML = @_template(this)
        @parentElement.appendChild node.firstChild
        @el = document.getElementById(@id)
        return

