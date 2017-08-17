
class SeriesPage
    @hash: 'series'

    constructor: (app) ->
        @app = app
        return

    enable: (param) ->
        @app.setMainStatus('Series page started')
        return

    disable: (param) ->
        @app.setMainStatus('Series page finished')
        return

#module.exports = SeriesPage
