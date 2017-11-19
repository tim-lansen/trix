
class FilesetRec extends Fileset

    @Colunms: [
        ['Folder', 'name']
        ['Created', 'creation_time']
        ['Modified', 'modification_time']
        ['Status', 'status']
        ['Action', 'action']
    ]

    @Status:
        0: 'UNDEFINED'
        1: 'NEW'
        2: 'INWORK'
        3: 'DONE'
        4: 'FAILED'

    constructor: (index, api_answer) ->
        # Fileset's properties
        @setup api_answer
        # Record's own properties
        @index = index
        @status_string = FilesetRec.Status[@status]
        return

    setup: (api_answer) ->
        @name = api_answer.name
        @creation_time = api_answer.creation_time
        @modification_time = api_answer.modification_time
        @status = api_answer.status
        if api_answer.contains('ctime')
            @guid = api_answer.guid
            @ctime = api_answer.ctime
            @mtime = api_answer.mtime
            @path = api_answer.path
            @files = api_answer.files
            @dirs = api_answer.dirs

    rowHTML: () ->
        html = '<tr class="files row row' + @index % 2 + ' ' + @status_string.toLowerCase() + '">'

        for col in FilesetRec.Colunms
            html += '<td>' + @[col[1]] + '</td>'
        html += '</tr>'
        return html

    dataHTML: () ->
        html = ''
        for d in @dirs
            html += '<p>DIR: ' + d + '</p>'
        for f in @files
            html += '<p>FILE: ' + f.name + ' ' + f.ctime + '/' + f.mtime + '</p>'
        return html


class FilesPage
    @hash: 'files'
    @ActionCell: 4

    constructor: (app) ->
        @app = app
        @filesets = []
        @fs_map = {}
        @fs_idx = undefined
        @fs_table = document.getElementById('files-table')
        @fs_data = document.getElementById('files-data')
        # detect action cell index
        for cell in @fs_table.rows[0].cells
            if cell.innerHTML.toLowerCase().indexOf('action') != -1
                FilesPage.ActionCell = cell.cellIndex
                break
        return

    enable: (param) ->
        @app.setMainStatus('Files page started')
        $('#files-table').bind('click', @click_table.bind(@))
        return

    disable: (param) ->
        @app.setMainStatus('Files page finished')
        $('#files-table').unbind('click')
        return

    unselect_row: ->
        if @fs_idx != undefined
            fs_elm = @fs_table.rows[@fs_idx + 1]
            fs_elm.removeClass('selected')
            @fs_idx = undefined
            @fs_data.innerHTML = ''
        return

    select_row: (row_idx) ->
        console.log('select_row ' + row_idx)
        @unselect_row()
        fs_elm = @fs_table.rows[row_idx]
        fs_elm.addClass('selected')
        @fs_idx = row_idx - 1
        return

    show_fileset: (tries=0) ->
        fs = @filesets[@fs_idx]
        if fs.ctime == 0
            tries ++
            @app.ws_api_trix.request(
                { 'method': 'fileset.get', 'params': {'name': fs.name} },
                ( (msg) ->
                    console.log 'fileset.get handler'
                    answer = msg.result
                    if !answer
                        console.log 'no results'
                        return
                    @filesets[@fs_idx].setup(answer)
                    @show_fileset(tries)
                    return
                ).bind(@)
            )
        else
            @fs_data.innerHTML = fs.dataHTML()
        return

    click_table: (e) ->
        td = e.target
        row_idx = td.parentNode.rowIndex
        if row_idx > 0
            fs_idx = row - 1
            col = td.cellIndex
            if fs_idx == @fs_idx
                if col == FilesPage.ActionCell
                    @action()
            else
                @select_row(fs_idx)
        return

    refresh: ->
        @unselect_row()
        $('#files-table').unbind('click')
        @app.ws_api_trix.request(
            { 'method': 'fileset.getList', 'params': {} },
            ( (msg) ->
                console.log 'fileset.getList handler'
                answer = msg.result
                i = undefined
                if !answer
                    console.log 'no results'
                    return
                html = ''
                html += '<tr>'

                for col in cols
                    html += '<th>' + col + '</th>'
                html += '</tr>'
                @fs_map = {}
                for i, ans of answer
                    fs = new FilesetRec(i, ans)
                    console.log(fs)
                    html += fs.rowHTML()
                    @fs_map[fs.guid] = i
                @fs_table.innerHTML = html
                $('#files-table').bind('click', @click_table.bind(@))
                return
            ).bind(@)
        )

#module.exports = FilesPage
