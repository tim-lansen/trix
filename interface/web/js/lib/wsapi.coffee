
class WSAPIStates
    @closed: 'closed'
    @opening: 'opening'
    @opened: 'opened'
    @connecting: 'connecting'
    @connected: 'connected'
    @authenticating: 'authenticating'
    @authenticated: 'authenticated'
    @authorizing: 'authorizing'
    @authorized: 'authorized'

class WSAPI
    @States: WSAPIStates

    constructor: (address, handlers) ->
        console.log address, handlers
        @address = address
        @handlers = handlers
        @messageId = 1
        @sessionId = null
        @requestPool = {}
        @ws = null
        @state = WSAPI.States.closed
        if ! @handlers.hasOwnProperty('states')
            @handlers.states = {}
        return

    wsApiSend: (msg) ->
        if typeof msg.id == 'undefined'
            msg.id = '' + @messageId
            @messageId++
        console.log 'wsApiSend', @address, msg
        @ws.send JSON.stringify(msg)
        return

    add_state_handler: (state, handler) ->
        if @handlers.states.hasOwnProperty(state)
            if Array.isArray(@handlers.states[state])
                @handlers.states[state].push handler
            else
                console.log 'Cannot add state handler'
        else
            @handlers.states[state] = [ handler ]
        return

    send: (msg) ->
        msg.id = '' + @messageId
        @messageId++
        m = JSON.stringify(msg)
        @ws.send m
        return

    beat: ->
        if @state == WSAPI.States.closed
            if @ws
                @ws.close()
            @state = WSAPI.States.opening
            @ws = new WebSocket(@address)
            @ws.onmessage = ((e) ->
                msg = e.data
                console.log 'onmessage ' + @address + ' ' + e.data
                #console.log('wsOnMessage: ' + msg);
                if msg
                    try
                        m = JSON.parse(msg)
                        if typeof @handlers.onmessage == 'function'
                            @handlers.onmessage @, m
                        else
                            console.log 'No handler for message: ' + m
                    catch err
                        console.log err
                return
            ).bind(@)
            @ws.onopen = (->
                @state = WSAPI.States.opened
                if typeof @handlers.onopen == 'function'
                    @handlers.onopen @
                return
            ).bind(@)
            @ws.onclose = (->
                @state = WSAPI.States.closed
                if typeof @handlers.onclose == 'function'
                    @handlers.onclose @
                return
            ).bind(@)
            @ws.onerror = (->
                @state = WSAPI.States.closed
                if typeof @handlers.onerror == 'function'
                    @handlers.onerror @
                return
            ).bind(@)
        else
            if @handlers.states
                # State beat handler may be a single function or an array of functions
                sths = @handlers.states[@state]
                if typeof sths == 'function'
                    sths @
                else if Array.isArray(sths)
                    i = 0
                    while i < sths.length
                        if typeof sths[i] == 'function'
                            sths[i] @
                        i++
        return

    close: ->
        if @ws
            @ws.close()
            @ws = null
        @state = WSAPI.States.closed
        return

    request: (req, callback) ->
        # Send message to api server
        if @state == WSAPI.States.authorized
            if callback != null
                req.id = Utils.UUID.generate()
                @requestPool[req.id] =
                    'request': req
                    'callback': callback
            req.id = '' + @messageId
            @messageId++
            @requestPool[req.id] =
                'request': req
                'callback': callback
            @wsApiSend req
        return

    connect: (req) ->
        if !req
            req = 'method': 'connect'
        @state = WSAPI.States.connecting
        @wsApiSend req
        return

    profile: (req) ->
        if !req
            req =
                'method': 'profile'
                'params': {}
        @wsApiSend req
        return

    force: (req) ->
        @wsApiSend req
        return

    authorize: (profile, device_token, serial_number) ->
        console.log 'authorize'
        @state = 'authorizing'
        @wsApiSend {
            'method': 'authorize',
            'params': {
                'phone_number': profile.phone_number,
                'name': profile.name,
                'profile_id': profile.id,
                'session_id': @sessionId,
                'device_token': device_token,
                'serial_number': serial_number
            }
        }

    auth: (profile, device_token, serial_number) ->
        console.log 'authorize'
        @state = WSAPI.States.authorizing
        @wsApiSend
            'method': 'authorize'
            'params':
                'phone_number': profile.phone_number
                'name': profile.name
                'profile_id': profile.id
                'session_id': @sessionId
                'device_token': device_token
                'serial_number': serial_number
        return

#module.exports = WSAPI
