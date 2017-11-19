module.exports = (grunt)->
    grunt.file.defaultEncoding = 'utf8'
    grunt.file.preserveBOM = false
    grunt.loadNpmTasks 'grunt-contrib-less'
    grunt.loadNpmTasks 'grunt-contrib-jade'
    grunt.loadNpmTasks 'grunt-contrib-watch'
    grunt.loadNpmTasks 'grunt-contrib-copy'
    grunt.loadNpmTasks 'grunt-contrib-clean'
    grunt.loadNpmTasks 'grunt-umd'
    grunt.loadNpmTasks 'grunt-browserify'
    #grunt.loadNpmTasks 'grunt-coffee'
    grunt.loadNpmTasks 'grunt-contrib-coffee'

    grunt.initConfig
        clean:
            build:
                ['build', 'dist']
            distd:
                ['D:\\storage\\web\\dist']
            distf:
                ['F:\\storage\\web\\dist']
        jade:
            build:
                options:
                    pretty: true
                    data: (dest, src)->
                        options = {}
                        return options

                files:
                    "dist/index.html": ["jade/index.jade"]

            client:
                options:
                    pretty: false
                    client: true
                    amd: false
                    namespace: 'jade_tmpl'

                    processName: ->
                        return 'dummy'

                files:
                    "build/jade_tmpl/interactionsPage.js": ["jade/pages/interactionsPage.jade"]
                    "build/jade_tmpl/filesPage.js":        ["jade/pages/filesPage.jade"]
                    "build/jade_tmpl/playerPage.js":       ["jade/pages/playerPage.jade"]
                    "build/jade_tmpl/seriesPage.js":       ["jade/pages/seriesPage.jade"]

        less:
            build:
                files:
                    "dist/css/main.css": "less/main.less"

        copy:
            build:
                files: [
                    {
                        # Copy PNGs to dist
                        expand: true
                        src: ['**/*.png']
                        cwd: 'less'
                        dest: 'dist/css'
                        filter: 'isFile'
#                    }, {
#                         Copy config
#                        expand: true
#                        src: ['api_config.json']
#                        dest: 'dist'
                    }, {
                        # Copy JavaScript and JSON files to build
                        expand: true
                        src: ['**/*.js', '**/*.json']
                        cwd: 'js'
                        dest: 'build'
                        filter: 'isFile'
                    }
                ]
            js:
                files: [
                    expand: true
                    src: ['**/*.js', '**/*.json']
                    cwd: 'js'
                    dest: 'build'
                    filter: 'isFile'
                ]
            distd:
                files: [
                    expand: true
                    src: '**'
                    cwd: 'dist'
                    dest: 'D:\\storage\\web\\dist'
                    filter: 'isFile'
                ]
            distf:
                files: [
                    expand: true
                    src: '**'
                    cwd: 'dist'
                    dest: 'F:\\storage\\web\\dist'
                    filter: 'isFile'
                ]

        umd:
            jade: {
                options: {
                    src: [
                        'build/jade_tmpl/interactionsPage.js'
                        'build/jade_tmpl/filesPage.js'
                        'build/jade_tmpl/playerPage.js'
                        'build/jade_tmpl/seriesPage.js'
                    ],
                    objectToExport: 'jade_tmpl.dummy'
                    deps: {
                        'default': [],
                        # 'amd': [{'jade': 'jade/lib/runtime.js'}],
                        'cjs': [{'jade/lib/runtime.js':'jade'}]
                        # global: ['foobar', {depName: 'param'}]
                    }
                }
            }

        coffee:
#            compile:
#                expand: true
#                flatten: false
#                cwd: 'js'
#                src: [
#                    'models/*.coffee'
##                    'pages/*.coffee'
##                    'pages/ui/*.coffee'
#                ]
#                dest: 'build'
#                ext: '.js'
#                options:
#                    bare: true
#                    join: false
            compile_joined:
                expand: true
                files:
                    'build/main.js': [
                        'js/lib/*.coffee'
                        'js/models_py/*.coffee'
                        'js/models/InteractionInternal.coffee'
                        'js/pages/ui/*.coffee'
                        'js/pages/interactions.coffee'
                        'js/pages/files.coffee'
                        'js/main.coffee'
                    ]
                options:
                    bare: true
                    join: true

        browserify:
            build:
                files:
                    'dist/main.js': ['build/main.js']
            test:
                files:
                    'dist/main.js': ['build/test.js']

        watch:
            jade:
                files: ['jade/*.jade']
                tasks: ['jade:build', 'browserify']
                options:
                    interrupt: true

            jade_templates:
                files: 'jade/pages/*.jade'
                tasks: ['jade:client', 'umd:jade', 'browserify']
                options:
                    interrupt: true

            js:
                files: ['js/**/*.js']
                tasks: ['browserify']
                options:
                    interrupt: true

            less:
                files: ['less/*.less']
                tasks: ['less']
                options:
                    interrupt: true

    grunt.registerTask 'default', 'watch'

    #grunt.registerTask 'coffee'

    grunt.registerTask 'build', ['clean:build', 'copy:build', 'coffee', 'less', 'jade', 'umd', 'browserify:build']
    grunt.registerTask 'distd', ['clean:distd', 'build', 'copy:distd', 'clean:build']
    grunt.registerTask 'distf', ['clean:distf', 'build', 'copy:distf', 'clean:build']
    grunt.registerTask 'test',  [               'copy:build', 'coffee', 'less', 'jade', 'umd', 'browserify:test']
