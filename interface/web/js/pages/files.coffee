


class FilesetRec extends Fileset

    @Colunms_fileset: [
        ['Folder', 'name', ' class="clickable"']
        ['Created', 'creation_time']
        ['Modified', 'modification_time']
        ['Status', 'status_string']
        ['Action', 'action', ' class="clickable"']
    ]

    @Colunms_data: [
        ['Filename', 'name']
        ['Created', 'ctime']
        ['Modified', 'mtime']
        ['Size', 'size']
    ]

    @Status:
        0: 'undefined'
        1: 'new'
        2: 'ignore'
        3: 'inwork'
        4: 'done'
        5: 'failed'

    constructor: (index) ->
        # Record's own properties
        @index = index
        @status_string = undefined
        return

    setup: (api_answer) ->
        @name = api_answer.name
        @guid = api_answer.guid
        @creation_time = api_answer.creation_time
        @modification_time = api_answer.modification_time
        @status = api_answer.status
        @status_string = FilesetRec.Status[@status]
        if api_answer.hasOwnProperty('ctime')
            @ctime = api_answer.ctime
            @mtime = api_answer.mtime
            @path = api_answer.path
            @files = api_answer.files
            @dirs = api_answer.dirs
        return

    rowHTML: ->
        html = '<tr class="files row row' + @index % 2 + ' ' + @status_string.toLowerCase() + '">'
        for col in FilesetRec.Colunms_fileset
            if col[1].indexOf('time') > 0
                value = secondsToDateTime(@[col[1]])
            else
                value = @[col[1]]
            cls = ''
            if col[2] != undefined
                cls = col[2]
            html += '<td'+cls+'>' + value + '</td>'
        html += '</tr>'
        return html

    dataTabHead: ->

    @dataHTML: (fsr=null) ->
        html = ''
        html += '<tr>'

        for col in FilesetRec.Colunms_data
            html += '<th>' + col[0] + '</th>'
        html += '</tr>'

        if fsr != null
            i = 0
            if fsr.dirs != null
                for d in fsr.dirs
                    html += '<tr class="files row row' + i % 2 + '">'
                    html += '<td>' + d + '</td>'
                    html += '<td></td>'
                    html += '<td></td>'
                    html += '<td>DIR</td>'
                    html += '</tr>'
                    i += 1
            if fsr.files != null
                for f in fsr.files
                    html += '<tr class="files row row' + i % 2 + '">'
                    for col in FilesetRec.Colunms_data
                        if col[1].indexOf('time') >= 0
                            value = secondsToDateTime(f[col[1]])
                        else if col[1].indexOf('size') >= 0
                            value = formatSize(f[col[1]])
                        else
                            value = f[col[1]]
                        html += '<td>' + value + '</td>'
                    html += '</tr>'
                    i += 1

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
        $('#files-refresh').bind('click', @refresh.bind(@))
        return

    disable: (param) ->
        @app.setMainStatus('Files page finished')
        $('#files-table').unbind('click')
        $('#files-refresh').unbind('click')
        return

    unselect_row: ->
        if @fs_idx != undefined
            fs_elm = @fs_table.rows[@fs_idx + 1]
            $(fs_elm).removeClass('selected')
            @fs_idx = undefined
            @fs_data.innerHTML = FilesetRec.dataHTML()
        return

    select_row: (row_idx) ->
        @unselect_row()
        fs_elm = @fs_table.rows[row_idx]
        $(fs_elm).addClass('selected')
        @fs_idx = row_idx - 1
        return

    show_fileset: ->
        fs = @filesets[@fs_idx]
        if !fs.ctime
            @app.ws_api_trix.request(
                { 'method': 'fileset.get', 'params': {'guid': fs.guid} },
                ( (msg) ->
                    console.log 'fileset.get handler'
                    answer = msg.result[0]
                    if !answer
                        console.log 'no results'
                        return
                    fs = @filesets[@fs_idx]
                    fs.setup(answer)
                    @fs_data.innerHTML = FilesetRec.dataHTML(fs)
                    return
                ).bind(@)
            )
        else
            @fs_data.innerHTML = FilesetRec.dataHTML(fs)
        return

    action: () ->
        console.log('Do something')
        return

    click_table: (e) ->
        td = e.target
        row_idx = td.parentNode.rowIndex
        if row_idx > 0
            fs_idx = row_idx - 1
            col = td.cellIndex
            if fs_idx == @fs_idx
                if col == FilesPage.ActionCell
                    @action()
            else if col == 0
                @select_row(row_idx)
                @show_fileset()
        return

    refresh: ->
        @unselect_row()
        $('#files-table').unbind('click')
        @filesets = []
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

                for col in FilesetRec.Colunms_fileset
                    html += '<th>' + col[0] + '</th>'
                html += '</tr>'
                @fs_map = {}
                for i, ans of answer
                    fs = new FilesetRec(i)
                    fs.setup(ans)
                    @filesets.push(fs)
                    html += fs.rowHTML()
                    @fs_map[fs.guid] = i
                @fs_table.innerHTML = html
                $('#files-table').bind('click', @click_table.bind(@))
                return
            ).bind(@)
        )

#module.exports = FilesPage
