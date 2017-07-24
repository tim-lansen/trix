"use strict";

class SeriesData
    constructor: (app) ->
        @app = app
        @seriesAll = {}
        @rightholders = app.shared.rightholders
        @rsse =
            'series': null
            'seasons': null
            'episodes': null
            'callback': null
        #this.api_rightholders_all = [];
        #this.api_rightholders = {};
        return

    refreshNapi: (callback) ->
        if @wsNapi.state == 'authorized'
            @wsNapi.request {
                'method': 'rightholders_all'
                'params': {}
            }, ((m) ->
                console.log 'SeriesData.refreshNapi f1'
                @api_rightholders_all = m.result.ids
                # Continue requesting rightholders
                window.setMainStatus 'Requesting rightholders data...'
                @wsNapi.request {
                    'method': 'rightholders'
                    'params': 'ids': @api_rightholders_all
                }, ((m) ->
                    console.log 'SeriesData.refreshNapi f2'
                    @api_rightholders = {}
                    @rightholdersSelectHTML = ''
                    i = 0
                    while i < m.result.length
                        # Rebuild from {"id": x, "name": "Warner Bros. Entertainment, Inc."}
                        # to x: {'name': 'Warner Bros. Entertainment, Inc.', 'legacy': 'Warner_Bros_Entertainment_Inc', 'alias': 'WB'}
                        rhId = m.result[i].id
                        rhName = m.result[i].name
                        rhAlias = undefined
                        rhLegacy = legalizeName(rhName)
                        if rhName of rightholdersAliases
                            rhAlias = rightholdersAliases[rhName]
                        else
                            rhAlias = rhLegacy
                        @api_rightholders[rhId] =
                            'name': rhName
                            'legacy': rhLegacy
                            'alias': rhAlias
                        @rightholdersSelectHTML += '<option value="' + rhId + '">' + rhName + '</option>'
                        i++
                    # Continue requesting movies IDs
                    window.setMainStatus 'Requesting list of movies...'
                    @wsNapi.request {
                        'method': 'movies_all'
                        'params': {}
                    }, ((m) ->
                        console.log 'SeriesData.refreshNapi f3'
                        @api_movies_all = m.result.ids
                        # Continue requesting movies data
                        window.setMainStatus 'Requesting movies data...'
                        @wsNapi.request {
                            'method': 'movies_extra'
                            'params': 'ids': @api_movies_all
                        }, ((m) ->
                            `var i`
                            console.log 'Get All Movies #5'
                            window.setMainStatus 'Rebuild data...'
                            @api_movies = {}
                            i = 0
                            while i < m.result.length
                                # Rebuild data
                                moStudio = m.result[i].rightholder_ids[0]
                                if !@api_movies.hasOwnProperty(moStudio)
                                    @api_movies[moStudio] = {}
                                @api_movies[moStudio][m.result[i].id] =
                                    'slug': m.result[i].slug
                                    'guid': m.result[i].id_guid
                                    'title': m.result[i].title
                                    'original_title': m.result[i].original_title
                                    'title_legacy': legalizeName(m.result[i].title)
                                    'original_title_legacy': legalizeName(m.result[i].original_title)
                                    'status': m.result[i].status
                                    'video': m.result[i].video
                                i++
                            if typeof callback == 'function'
                                callback()
                            return
                        ).bind(this)
                        return
                    ).bind(this)
                    return
                ).bind(this)
                return
            ).bind(this)
        else
            window.setMainStatus 'Not authorized'
        return

    refresh: (callback) ->
        wsNapi = @app.shared.wsNapi
        @rsse.callback = callback
        console.log 'SeriesData requesting series_all'
        wsNapi.request {
            'method': 'series_all'
            'params': {}
        }, ((m) ->
            console.log 'SeriesData requesting series_extra'
            all_series_ids = m.result.ids
            wsNapi.request {
                'method': 'series_extra'
                'params': 'ids': all_series_ids
            }, ((m) ->
                @rsse.series = m.result
                @rebuild()
                return
            ).bind(this)
            return
        ).bind(this)
        console.log 'SeriesData requesting seasons_all'
        wsNapi.request {
            'method': 'seasons_all'
            'params': {}
        }, ((m) ->
            console.log 'SeriesData requesting seasons_extra'
            all_seasons_ids = m.result.ids
            wsNapi.request {
                'method': 'seasons_extra'
                'params': 'ids': all_seasons_ids
            }, ((m) ->
                @rsse.seasons = m.result
                @rebuild()
                return
            ).bind(this)
            return
        ).bind(this)
        console.log 'SeriesData requesting episodes_all'
        wsNapi.request {
            'method': 'episodes_all'
            'params': {}
        }, ((m) ->
            console.log 'SeriesData requesting episodes_extra'
            all_episodes_ids = m.result.ids
            wsNapi.request {
                'method': 'episodes_extra'
                'params': 'ids': all_episodes_ids
            }, ((m) ->
                @rsse.episodes = m.result
                @rebuild()
                return
            ).bind(this)
            return
        ).bind(this)
        return

    rebuild: ->
        if @rsse.series == null or @rsse.seasons == null or @rsse.episodes == null
            return
        console.log 'SeriesData ready to rebuild'
        # Resulting object should look like this:
        # {
        #    <series_identity>: series_data + {'seasons': seasons_data + {'episodes': episodes_data}}
        # }
        # seasons_data = {index: season_data, ...}
        # episodes_data = {index: episode_data, ...}
        series = @rsse.series
        seasons = @rsse.seasons
        episodes = @rsse.episodes
        # helper object
        # series_id: "series_identity"
        lSeasons = {}
        lEpisodes = {}
        i = undefined
        # Build helpers
        i = 0
        while i < series.length
            series[i].identity = series[i].original_title + '@' + series[i].start_year
            series[i].seasons = {}
            @seriesAll[series[i].id] = series[i]
            i++
        i = 0
        while i < seasons.length
            seasons[i].episodes = {}
            @seriesAll[seasons[i].series].seasons[seasons[i].index] = seasons[i]
            lSeasons[seasons[i].id] = i
            i++
        i = 0
        while i < episodes.length
            seasons[lSeasons[episodes[i].season]].episodes[episodes[i].index] = episodes[i]
            i++
        console.log @seriesAll
        if typeof @rsse.callback == 'function'
            @rsse.callback()
        return

module.exports = SeriesData
