
UpdateObjectWithJSON = (obj, json) ->
    for k, v of json
        if obj.hasOwnProperty(k)
            obj[k] = v
        else
            console.log 'UpdateObjectWithJSON: object '+obj+' has no property '+k
