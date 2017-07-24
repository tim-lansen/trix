'use strict'

class LiveCrop
    constructor: ->
        # Source dims
        @srcW = 960
        @srcH = 540
        @minX = 0
        @maxX = 960
        @minY = 0
        @maxY = 540
        @scaleX = 1.0
        @scaleY = 1.0
        # liveCrop front array
        @liveCrop = [
            0
            960
            0
            540
        ]
        return

    setVideoSrcDimensions: (width, height) ->
        @srcW = width
        @srcH = height
        @scaleX = (@maxX - (@minX)) / width
        @scaleY = (@maxY - (@minY)) / height
        @liveCrop = [
            0
            width
            0
            height
        ]
        return

    setVideoSrcCrop: (x1, x2, y1, y2) ->
        @liveCrop = [
            x1
            x2
            y1
            y2
        ]
        return

    snapLiveCrop: (val) ->
        l = undefined
        l = @liveCrop[1] - (@liveCrop[0])
        dl = l % val
        if dl > 0
            l -= dl
            @liveCrop[0] += parseInt(dl / 2)
            @liveCrop[1] = @liveCrop[0] + l
        l = @liveCrop[3] - (@liveCrop[2])
        dl = l % val
        if dl > 0
            l -= dl
            @liveCrop[2] += parseInt(dl / 2)
            @liveCrop[3] = @liveCrop[2] + l
        return

    updateCropString: ->
        crop = [
            @liveCrop[1] - (@liveCrop[0])
            @liveCrop[3] - (@liveCrop[2])
            @liveCrop[0]
            @liveCrop[2]
        ]
        # Update crop string in document
        document.getElementById('pro-video-crop').innerHTML = crop.join(':')
        return

    updateLiveCropX: (v, r) ->
        x = v - 4
        if x < @minX
            x = @minX
        else if x > @maxX
            x = @maxX
        @liveCrop[r] = parseInt((x - (@minX)) / @scaleX)
        @updateCropString()
        x + 4

    updateLiveCropY: (v, r) ->
        y = v - 4
        if y < @minY
            y = @minY
        else if y > @maxY
            y = @maxY
        @liveCrop[r] = parseInt((y - (@minY)) / @scaleY)
        @updateCropString()
        y + 4

    positionCropLines: ->
        v = undefined
        v = 4 + @minX + @liveCrop[0] * @scaleX
        document.getElementById('crop-x1').style.left = v + 'px'
        v = 4 + @minX + @liveCrop[1] * @scaleX
        document.getElementById('crop-x2').style.left = v + 'px'
        v = 4 + @minY + @liveCrop[2] * @scaleY
        document.getElementById('crop-y1').style.top = v + 'px'
        v = 4 + @minY + @liveCrop[3] * @scaleY
        document.getElementById('crop-y2').style.top = v + 'px'
        return

module.exports = LiveCrop
