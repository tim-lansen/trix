
class MoviesPage
    @hash: 'movies'

    constructor: (app) ->
        @app = app
        return

    enable: (param) ->
        @app.setMainStatus('Movies page started')
        return

    disable: (param) ->
        @app.setMainStatus('Movies page finished')
        return

#module.exports = MoviesPage
