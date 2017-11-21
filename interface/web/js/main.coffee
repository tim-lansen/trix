
ApiConfig = require('./api_config')


class AppInterface
#    @moviesData: null,
#    @seriesData: null,
#    @rightholders: null,
    @ws_api_trix: null,
    @ws_api: null,
    @update:
        movies_extra: []
    @setMainStatus: null


class Profile
    constructor: ->
        @id = null
        @phone_number = '9671604001'
        @name = 'tim.lansen'
        @authorized = false
        return

class Utils
    @WSAPI    : WSAPI
    @UUID     : UUID
    @legalize : Legalize

class Templates
    @templates:
        interactionsPage: require('../build/jade_tmpl/interactionsPage')
        filesPage:        require('../build/jade_tmpl/filesPage')
        playerPage:       require('../build/jade_tmpl/playerPage')
        seriesPage:       require('../build/jade_tmpl/seriesPage')
    @get: (name) ->
        return @templates[name + 'Page']

# Pages store class
class Pages
    @pages: {}
    @interface: null

    # index comes from sections
    @add: (page_constructor) ->
        if !page_constructor
            console.log('No constructor')
            page_constructor = class dummy
                @hash: 'dummy'+Object.keys(Pages.pages).length
        hash = page_constructor.hash
        if @pages.hasOwnProperty(hash)
            console.log('Page '+hash+' is already stored to Pages')
        else
            @pages[hash] = {
                cnst: page_constructor
                page: null
            }

    # Get page instance by name
    @get: (hash) ->
        if @pages.hasOwnProperty(hash)
            #return @pages[hash].get()
            if ! @pages[hash].page
                console.log('Creating instance of: '+@pages[hash].cnst.name+', hash: '+hash)
                @pages[hash].page = new @pages[hash].cnst(@interface)
            return @pages[hash].page
        return null

class App extends AppInterface
    @serial_number: null
    @device_token : null
    @pages: Pages
    @sections: [
        {capt: 'Files',      hash: 'files',      constructor: FilesPage, push: 'fileset'}
        #{capt: 'Series',      hash: 'series',      constructor: require('./pages/series')}
        {capt: 'Interactions', hash: 'interactions', constructor: InteractionsPage}
        {capt: 'Tasks',       hash: 'monitor',     constructor: null}
        {capt: 'Profiles',    hash: 'profiles',    constructor: null}
    ]
    @pushHandlers: {}
    @currentPage: null
    @currentHash: null
    @profile: new Profile()
    #@shared: Shared

    @run: (window) ->
        @serial_number = Utils.UUID.generate()
        @device_token = Utils.UUID.generate()
        console.log @serial_number
        console.log @device_token
        @init window
        return

    @check_section: (s) ->
        if !(s.hasOwnProperty('capt') && s.hasOwnProperty('hash'))
            console.log('Bad section record: '+s.toString())
            return false
        if ! s.constructor
            console.log('Section '+s.capt+' has no constructor')
            return false
        s.constructor.hash = s.hash
        return true

    @init: (window) ->
        console.log 'App.init(window)'

        Pages.interface = App

        html_select = ''
        html_sections = ''
        i = 0
        for s in @sections
            if ! @check_section(s)
                s.capt = 'Dummy_'+i
                s.hash = 'dummy_'+i
                i++
                html_select += '<span>'+s.capt+'</span>'
            else
                html_select += '<span class="select_page" id="sel_'+s.hash+'" onclick="window.location.hash=\''+s.hash+'\'">'+s.capt+'</span>'
                html_sections += '<section id='+s.hash+' src="pages/'+s.hash+'.htm"></section>'
                if s.hasOwnProperty('push')
                    s.constructor.push = s.push
                @pages.add(s.constructor)

        document.getElementById('selection_pane').innerHTML = html_select
        document.getElementById('sections').innerHTML = html_sections

        $(window).on 'hashchange', (->
            @hashChanged window.location.hash
            return
        ).bind(@)

        @init_api_trix()
        #@init_api()
        console.log 'Start timer: ' + @ws_api_trix
        @heartBeatId = setInterval(@heartBeat.bind(@), 1000);

        @hashChanged(window.location.hash)
        return

    @heartBeat: ->
        if @ws_api_trix
            @ws_api_trix.beat()

    @updateProfile: (data) ->
        @profile.id = data.id
        n = []
        if data.personal.first_name
            n.push data.personal.first_name
        if data.personal.last_name
            n.push data.personal.last_name
        n.push '['+data.personal.username+']'
        @profile.name = n.join ' '
        @profile.phone_number = data.contacts.phone_number
        return

    @setMainStatus: (status) ->
        try
            document.getElementById('main-status').innerHTML = status
        catch e
            console.log e
        return

    @switchPage: (hash) ->
        if @currentPage # && @pages[@currentPage]              # Disable previous page
            console.log 'Deactivating page "'+@currentPage.hash+'"'
            try
                @currentPage.disable()
            catch e
                console.log '  page '+hash+' has faulty "disable" function'
                console.log e
        console.log 'Activating page "'+hash+'"'                        # Activate the new page
        page = @pages.get(hash)
        if page.hasOwnProperty('push') and !@pushHandlers.hasOwnProperty(page.push)
            @pushHandlers[page.push] = page
        if page
            console.log("%o", page)
            try
                page.enable()
            catch e
                console.log '  page '+hash+' has faulty "enable" function'
                console.log e
        else
            console.log '  page constructor not found'
        $(document.body).attr('page', hash).find('section').removeClass('active').filter('section#' + hash).addClass 'active'
        @currentPage = page
        return

    @hashChanged: (hashtag) ->
        if hashtag == ''
            return
        re = /#([-0-9A-Za-z]+)(:(.+))?/
        match = re.exec(hashtag)
        if match.length == 0
            console.log('bad hash: '+hashtag)
        else
            hash = match[1]
            param = match[3]
            try
                $('#sel_' + @currentHash).removeClass 'current'
                $('#sel_' + hash).addClass 'current'
            catch e
                console.log e
            @currentHash = hash

            $page = $(document.body).find('section#' + hash)
            template = Templates.get(hash)
            if template
                if $page.find('>:first-child').length == 0
                    console.log hash, Templates.templates
                    $page.html template(param)
                @switchPage hash
            else
                $page.html "can't find template: " + hash
        return

    @init_api_trix: ->
        trixServerAddress = undefined
        trixServerAddress = 'ws://' + ApiConfig.apiServer.host + ':' + ApiConfig.apiServer.port + '/'
        console.log trixServerAddress
        @ws_api_trix = new Utils.WSAPI(
            trixServerAddress,
            {
                onclose: ( -> document.getElementById('trix-status').innerHTML = 'TRIX: closed' )
                onerror: ( -> document.getElementById('trix-status').innerHTML = 'TRIX: error' )
                onopen:  ( -> document.getElementById('trix-status').innerHTML = 'TRIX: opened' )
                onmessage: ((wsapi, msg) ->
                    if msg.error
                        wsapi.close()
                        throw msg.error
                    switch msg.method
                        when 'connect'
                            wsapi.sessionId = msg.result.session_id
                            wsapi.state = 'connected'
                            document.getElementById('trix-status').innerHTML = 'TRIX: connected'
                        when 'authorize'
                            wsapi.state = 'authorized'
                            @setMainStatus 'Authorized'
                            document.getElementById('trix-status').innerHTML = 'TRIX: Authorized'
                        when 'push'
#                            push message = {
#                                'method': 'push',
#                                'push': 'fileset',
#                                'params': {...}
#                            }
                            instance = @pushHandlers[msg.push]
                            pushHandler = instance.pushHandler
                            if typeof pushHandler == 'function'
                                pushHandler(instance, msg.params)
                        else
                            if msg.id and wsapi.requestPool.hasOwnProperty(msg.id)
                                if typeof wsapi.requestPool[msg.id].callback == 'function'
                                    wsapi.requestPool[msg.id].callback(msg)
                                delete wsapi.requestPool[msg.id]

                    return
                ).bind(@)
                states:
                    opened: ((wsapi) -> wsapi.connect())
                    connected: ((wsapi) -> # authorize if we have user data
                        if ! @profile.authorized
                            wsapi.authorize @profile, @device_token, @serial_number
                        return
                    ).bind(@)
            }
        )
        return


do (window) ->
    'use strict'
    App.run(window)
    return
