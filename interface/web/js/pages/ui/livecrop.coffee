#'use strict'

class LiveCrop
    constructor: ->
        @canW = 960
        @canH = 540
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
            @canW
            0
            @canH
        ]
#        @cropLines = [
#            4 + @minX
#            4 + @maxX
#            4 + @minY
#            4 + @maxY
#        ]
#        @snap = 4
        return

    setVideoSrcDimensions: (width, height) ->
        @srcW = width
        @srcH = height
        aspect_src = parseInt(10000.0 * width / height)
        aspect_can = parseInt(10000.0 * @canW / @canH)

#        if aspect_src == aspect_can
        @scaleX = @canW / width
        @scaleY = @canH / height
        @minX = 0
        @minY = 0
        @maxX = @canW
        @maxY = @canH

        # Change verticals
        if aspect_src > aspect_can
            @scaleY = @scaleX
            h = height * @scaleY
            @minY = parseInt((@canH - h) / 2)
            @maxY = @minY + parseInt(h)
        else if aspect_src < aspect_can
            @scaleX = @scaleY
            w = width * @scaleX
            @minX = parseInt((@canW - w) / 2)
            @maxX = @minX + parseInt(w)

        @liveCrop = [
            0
            width
            0
            height
        ]
#        @cropLines = [
#            4 + @minX
#            4 + @maxX
#            4 + @minY
#            4 + @maxY
#        ]
        return

    setVideoSrcCrop: (x1, x2, y1, y2) ->
        @liveCrop = [
            x1
            x2
            y1
            y2
        ]
#        @cropLines = [
#            4 + @minX + parseInt(x1 * @scaleX)
#            4 + @minX + parseInt(x2 * @scaleX)
#            4 + @minY + parseInt(y1 * @scaleY)
#            4 + @minY + parseInt(y2 * @scaleY)
#        ]
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

    updateCropDetect: (cd) ->
        cd.w = @liveCrop[1] - (@liveCrop[0])
        cd.h = @liveCrop[3] - (@liveCrop[2])
        cd.x = @liveCrop[0]
        cd.y = @liveCrop[2]
        cd.sar = @scaleX/@scaleY
        cd.aspect = ((@liveCrop[1] - (@liveCrop[0]))/@scaleX) / ((@liveCrop[3] - (@liveCrop[2]))/@scaleY)
        console.log(cd)
        return

    updateLiveCropX: (v, r) ->
        if isNaN(v)
            return
#        if v > @cropLines[r]
#            v += @snap
#        else if v < @cropLines[r]
#            v -= @snap
#        else
#            return
#        @cropLines[r] = v
        x = v - 4
        if x < @minX
            x = @minX
        else if x > @maxX
            x = @maxX
        @liveCrop[r] = parseInt((x - (@minX)) / @scaleX)
        @updateCropString()
        x + 4

    updateLiveCropY: (v, r) ->
        if isNaN(v)
            return
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
#        document.getElementById('crop-x1').style.left = @cropLines[0] + 'px'
#        document.getElementById('crop-x2').style.left = @cropLines[1] + 'px'
#        document.getElementById('crop-y1').style.left = @cropLines[2] + 'px'
#        document.getElementById('crop-y2').style.left = @cropLines[3] + 'px'
        return

