
$ = require('jquery')
AppInterface = require('./app_interface')

class Profile
    constructor: ->
        @id = null
        @phone_number = '9671604001'
        @name = 'tim.lansen'
        @authorized = false
        return

class Models
    @Rightholders : require('./models/Rightholders')
    @MoviesData   : require('./models/MoviesData')
    @SeriesData   : require('./models/SeriesData')

class Utils
    @WSAPI    : require('./lib/wsapi')
    @UUID     : require('./lib/uuid')
    @legalize : require('./lib/legalize')

class Templates
    @templates:
        interactionPage: require('../build/jade_tmpl/interactionPage')
        moviesPage:      require('../build/jade_tmpl/moviesPage')
        playerPage:      require('../build/jade_tmpl/playerPage')
        seriesPage:      require('../build/jade_tmpl/seriesPage')
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
        {capt: 'Movies',      hash: 'movies',      constructor: require('./pages/movies')}
        {capt: 'Series',      hash: 'series',      constructor: require('./pages/series')}
        {capt: 'Interaction', hash: 'interaction', constructor: require('./pages/interaction')}
        {capt: 'Tasks',       hash: 'monitor',     constructor: null}
        {capt: 'Profiles',    hash: 'profiles',    constructor: null}
    ]
    @currentPage: null
    @currentHash: null
    @profile: new Profile()
    #@shared: Shared

    @run: (window) ->
        @serial_number = Utils.UUID.generate()
        @device_token = Utils.UUID.generate()
        console.log @serial_number
        console.log @device_token
        console.log Utils.legalize.legalize('йцукенг')
        @init(window)
        return

    @check_section: (s) ->
        if !(s.hasOwnProperty('capt') && s.hasOwnProperty('hash'))
            console.log('Bad section record: '+s.toString())
            return false
        else if ! s.constructor
            console.log('Section '+s.capt+' has no constructor')
            #return false
        else if s.hash != s.constructor.hash
            console.log('Section '+s.capt+' constructor\'s name does not match hash: '+s.constructor.hash)
            s.constructor.hash = s.hash
        return true

    @init: (window) ->
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
                @pages.add(s.constructor)

        document.getElementById('selection_pane').innerHTML = html_select
        document.getElementById('sections').innerHTML = html_sections

        $(window).on 'hashchange', (->
            @hashChanged window.location.hash
            return
        ).bind(@)

        @init_api_trix()
        @init_api()

        #@heartBeatId = setInterval(this.heartBeat.bind(this), 1000);

        @hashChanged(window.location.hash)
        return

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
        if document.URL.startsWith('file') or document.URL.startsWith('localhost') or document.URL.startsWith('http://localhost')
            trixServerAddress = 'ws://localhost:8001/'
        else
            trixServerAddress = 'ws' + document.URL.match(/http(:\/\/.+?)\//i)[1] + ':8001/'
        @ws_api_trix = new Utils.WSAPI(
            trixServerAddress,
            {
                onclose: ( -> document.getElementById('trix-status').innerHTML = 'TRIX: closed' )
                onerror: ( -> document.getElementById('trix-status').innerHTML = 'TRIX: error' )
                onopen:  ( -> document.getElementById('trix-status').innerHTML = 'TRIX: opened' )
                onmessage: ((wsapi, msg) ->
                    method = msg.method
                    switch method
                        when 'connect'
                            if msg.error
                                document.getElementById('trix-status').innerHTML = 'TRIX: connection error'
                                wsapi.close()
                            else
                                wsapi.state = 'connected'
                                wsapi.sessionId = msg.result.session_id
                                document.getElementById('trix-status').innerHTML = 'TRIX: connected'
                        when 'authorize'
                            if msg.error
                                wsapi.close()
                            else
                                wsapi.state = 'authorized'
                                @setMainStatus 'Authorized'
                                document.getElementById('trix-status').innerHTML = 'TRIX: Authorized'
                        else
                            if msg.id and wsapi.requestPool[msg.id]
                                if typeof wsapi.requestPool[msg.id].callback == 'function'
                                    wsapi.requestPool[msg.id].callback msg
                                    delete wsapi.requestPool[msg.id]
                    return
                ).bind(@)
                states:
                    opened: ( (wsapi) -> wsapi.connect() )
                    connected: ((wsapi) -> # authorize if we have user data
                        if @profile.authorized
                            wsapi.authorize @profile, device_token, serial_number
                        return
                    ).bind(@)
            }
        )
        return

    @init_api: ->
        state_handlers = {}
        state_handlers[Utils.WSAPI.States.authenticated] = [
            ( (wsapi) -> # Check authority
                wsapi.state = wsapi.States.authorizing
                wsapi.request({"method": "widgets_all", "params": {}})
            ).bind(@)
        ]
        state_handlers[Utils.WSAPI.States.authorized] = [
            ( (wsapi) ->
                if !@rightholders # create models
                    @rightholders = new Models.Rightholders(@)
                    @moviesData = new Models.MoviesData(@)
                    @seriesData = new SeriesData(@)
                    # Request everything
                    @rightholders.refresh(-> @moviesData.refresh(-> @seriesData.refresh(-> @setMainStatus('OK'))))
            ).bind(@)
        ]
        @ws_api = new Utils.WSAPI(
            'ws://api.localhost',
            {
                onclose: ( (wsapi) -> document.getElementById('napi-status').innerHTML = "API: " + wsapi.state ).bind(@)
                onerror: ( (wsapi) -> document.getElementById('napi-status').innerHTML = "API: " + wsapi.state ).bind(@)
                onopen: ( (wsapi) ->
                    wsapi.connect(
                        "method": "connect"
                        "params":
                            "version": "2"
                            "device_token": @device_token
                            "application":
                                "name": "web_admin"
                                "version": "4.0.1"
                            "device_info":
                                "serial_number": @serial_number
                                "type": "pc"
                                "name": "PC"
                                "model": "PC"
                    )
                    document.getElementById('napi-status').innerHTML = "API: " + wsapi.state
                ).bind(@)
                onmessage: ( (wsapi, msg) ->
                    console.log(msg)
                    switch msg.method
                        when 'connect'
                            if msg.error
                                console.log('Failed to connect: ' + msg.error)
                                wsapi.close()
                            else
                                wsapi.state = Utils.WSAPI.States.connected
                                wsapi.sessionId = msg.session_id
                                wsapi.profile()
                        when 'profile'
                            if msg.error
                                console.log('Failed to get profile: ' + msg.error)
                                wsapi.close()
                            else if msg.result.contacts.phone_number == null
                                # Have to auth by sms
                                @profile.phone_number = prompt("Your cell phone number", "+79671604001")
                                wsapi.state = Utils.WSAPI.States.authenticating
                                wsapi.force({"method": "login_phone_start", "params": {"phone": @profile.phone_number}})
                            else
                                wsapi.state = Utils.WSAPI.States.authenticated
                                @updateProfile(msg.result)
                        when 'widgets_all'
                            # Check authority
                            if msg.error
                                console.log('User is not authorized by API')
                                wsapi.close()
                            else
                                console.log('User is authorized by API')
                                @profile.authorized = true
                                wsapi.state = Utils.WSAPI.States.authorized
                        when 'login_phone_start'
                            # Authenticating phase #1
                            if msg.error
                                console.log('Login failed: '+msg.error)
                                wsapi.close()
                            else
                                console.log('Sending SMS')
                                wsapi.force({"method": "login_phone_send", "params": {"action_id": msg.result.action_id}})
                        when 'login_phone_send'
                            # Authenticating phase #2
                            if msg.error
                                console.log('Login failed: '+msg.error)
                                wsapi.close()
                            else
                                console.log('Waiting for PIN')
                                pin = prompt("Code from SMS", "")
                                wsapi.force({
                                    "method": "login_phone_sms_code_check"
                                    "params":
                                        "phone": @profile.phone_number
                                        "sms_code": pin
                                })
                        when 'login_phone_sms_code_check'
                            # Authenticating phase #3
                            if msg.error
                                console.log('Login failed: '+msg.error)
                                wsapi.close()
                                wsapi.beat()
                            else
                                wsapi.state = Utils.WSAPI.States.authenticated
#                        when 'update'
#                            # TODO: update rightholders/movies/series data
#                            for (var i in msg.params.data) {
#                            switch (msg.params.data[i].data_type) {
#                                case 'profile':
#                            // Update profile's data
#                            this.updateProfile(msg.params.data[i].update);
#                            // Check authority
#                            wsapi.state = Utils.WSAPI.States.authorized
#                            wsapi.request({"method": "widgets_all", "params": {}});
#                            break;
#                        when 'movies_extra'

                    if msg.id && wsapi.requestPool[msg.id]
                        if typeof(wsapi.requestPool[msg.id].callback) == 'function'
                            wsapi.requestPool[msg.id].callback(msg)
                            delete wsapi.requestPool[msg.id]

                    document.getElementById('top').className = "top " + wsapi.state
                    document.getElementById('napi-status').innerHTML = "API: " + wsapi.state
                ).bind(@)
                states: state_handlers
            }
        )
        return


do (window) ->
    'use strict'
    App.run(window)
    return
