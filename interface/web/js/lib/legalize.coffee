class Legalize
    @legacy: /[^&!0-9a-zA-Z]/g
    @strip: /^\s+|\s+$/g
    @space: /\s+/g
    @camspace: /\s+(.)/g
    @src1: 'ъ  ь  э  щ   ш  ч  ц  ю  я  ё  ж  ы а б в г д е з и й к л м н о п р с т у ф х'.split(RegExp(' +', 'g'))
    @dst1: 'h- s- e- sсh sh ch cz yu ya yo zh y a b v g d e z i j k l m n o p r s t u f h'.split(RegExp(' +', 'g'))
    @src2: '&   !'.split(RegExp(' +', 'g'))
    @dst2: 'and .-'.split(RegExp(' +', 'g'))

    @legalize: (text) ->
        t = text.toLowerCase()
        x = undefined
        # Transliterate
        x = 0
        while x < Legalize.src1.length
            t = t.split(Legalize.src1[x]).join(Legalize.dst1[x])
            x++
        # Replace non-legacy symbols by spaces
        t = t.replace(Legalize.legacy, ' ')
        # Make every word's first char Upper Case, then strip string
        t = (' ' + t).replace(Legalize.camspace, ($1) ->
            $1.toUpperCase()
        ).replace(Legalize.space, ' ').replace(Legalize.strip, '')
        # Replace special symbols by their legacy representations
        x = 0
        while x < Legalize.src2.length
            t = t.split(Legalize.src2[x]).join(Legalize.dst2[x])
            x++
        # Reverse article
        tt = t.split(' ')
        if tt.length > 1
            if tt[0] == 'The' or tt[0] == 'An' or tt[0] == 'A'
                tt.push tt[0]
                tt.shift()
            t = tt.join('_')
        t

module.exports = Legalize
