
class UUID
    # This is static method
    @generate: ->
        d = 0x100000000 + Math.random()*0xffffffff|0
        res = d.toString(16).substr(1)
        d = 0x100000000 + Math.random()*0xffffffff|0
        v = d.toString(16)
        res += '-' + v.substr(1, 4) + '-' + v.substr(5, 4)
        d = 0x100000000 + Math.random()*0xffffffff|0
        v = d.toString(16)
        res += '-' + v.substr(1, 4) + '-' + v.substr(5, 4)
        d = 0x100000000 + Math.random()*0xffffffff|0
        res += d.toString(16).substr(1)
        res


#module.exports = UUID
