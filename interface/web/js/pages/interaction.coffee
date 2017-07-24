
#AppInterface = require('../app_interface')

class InteractionPage
    @hash: 'interaction'
    @LiveCrop          = require('./ui/live_crop')
    @InteractionPlayer = require('./ui/interaction_player')

    @Interaction       = require('../models/Interaction')


    constructor: (app) ->
        @app = app
        return

    enable: (param) ->
        @app.setMainStatus('Interaction page started')
        return

    disable: (param) ->
        @app.setMainStatus('Interaction page finished')
        return

    echo: ->
        console.log('My hash:' + InteractionPage.hash)
        console.log('My app: '+@app)
        return

module.exports = InteractionPage
