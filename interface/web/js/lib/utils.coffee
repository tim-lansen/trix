

zeroez = '0000000000000000'

zpad = (strnum, size) ->
# Up to 16 leading zeroes
    x = strnum.toString()
    if x.length < size
        x = zeroez.substring(0, size - (x.length)) + x
    x

odev = (number) ->
    if number % 2 then 'odd' else 'even'

class Timecode
    @rx = /^(\d{2}):(\d{2}):(\d{2}\.\d+)$/
    @seconds: (tc) ->
        res = rx.exec(tc)
        if res == null
            return NaN
        sec = parseInt(res[1]) * 3600 + parseInt(res[2]) * 60 + parseFloat(res[3])
        sec

    @timecode: (seconds) ->
        tm = parseInt(seconds / 60)
        h = parseInt(tm / 60)
        m = tm - (h * 60)
        s = parseInt(seconds) - (tm * 60)
        ms = parseInt(1000 * (seconds - parseInt(seconds)))
        tc = zpad(h, 2) + ':' + zpad(m, 2) + ':' + zpad(s, 2) + '.' + zpad(ms, 3)
        tc

createStyleSequence = (baseName, h, s, l, a, hH, sH, lH, aH, rotOddEvenH, gainOddEvenL, steps) ->
    css = ''
    ho = 0
    lig = 0
    # var sat = 0;
    # var oel = 0;
    i = 0
    while i < steps
        oe = i % 2
        ho = (h + (i - oe) * 360 / steps + rotOddEvenH * oe) % 360
        lig = l + gainOddEvenL * oe
        css += '.' + baseName + padz(i, 2) + '{background-color:hsla(' + ho + ',' + s + '%,' + lig + '%,' + a + ');} '
        ho = (hH + (i - oe) * 360 / steps + rotOddEvenH * oe) % 360
        lig = lH + gainOddEvenL * oe
        css += '.' + baseName + padz(i, 2) + ':hover{background-color:hsla(' + ho + ',' + sH + '%,' + lig + '%,' + aH + ');} '
        i++
    style = document.createElement('style')
    if style.styleSheet
        style.styleSheet.cssText = css
    else
        style.appendChild document.createTextNode(css)
    document.getElementsByTagName('head')[0].appendChild style
    return