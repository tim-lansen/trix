'use strict'
#$ = require('jquery')

class Utils
    @WSAPI    : require('./lib/wsapi')
    @UUID     : require('./lib/uuid')
    @legalize : require('./lib/legalize')

Inter = require('./pages/interaction')
inter1 = new Inter(null)
inter2 = new Inter(2)
inter3 = new Inter(3)
inter1.echo()
inter2.echo()
inter3.echo()


class App
    #@WSAPI: require('./lib/wsapi')
    #@uuid: require('./lib/uuid')
    #@legalize: require('./lib/legalize')
    #@$: require('jquery')
    @serial_number: null
    @device_token: null
    @run_static: ->
        @serial_number = Utils.UUID.generate()
        @device_token = Utils.UUID.generate()
        console.log App.serial_number
        console.log App.device_token
        console.log Utils.legalize.legalize('йцукенг')
        re = /#([-0-9A-Za-z]+)(:(.+))?/
        match = re.exec('#dfesfweg:param1:param2')
        console.log match
        return

    run: ->
        @serial_number = Utils.UUID.generate()
        @device_token = Utils.UUID.generate()


do (window) ->
    App.run()
    return
