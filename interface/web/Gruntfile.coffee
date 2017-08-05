﻿module.exports = (grunt)->
    grunt.file.defaultEncoding = 'utf8'
    grunt.file.preserveBOM = false
    grunt.loadNpmTasks 'grunt-contrib-less'
    grunt.loadNpmTasks 'grunt-contrib-jade'
    grunt.loadNpmTasks 'grunt-contrib-watch'
    grunt.loadNpmTasks 'grunt-contrib-copy'
    grunt.loadNpmTasks 'grunt-umd'
    grunt.loadNpmTasks 'grunt-browserify'
    #grunt.loadNpmTasks 'grunt-coffee'
    grunt.loadNpmTasks 'grunt-contrib-coffee'

    grunt.initConfig
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
                    "build/jade_tmpl/interactionPage.js": ["jade/pages/interactionPage.jade"]
                    "build/jade_tmpl/moviesPage.js":      ["jade/pages/moviesPage.jade"]
                    "build/jade_tmpl/playerPage.js":      ["jade/pages/playerPage.jade"]
                    "build/jade_tmpl/seriesPage.js":      ["jade/pages/seriesPage.jade"]

        less:
            build:
                files:
                    "dist/css/main.css": "less/main.less"

        copy:
            pics:
                files: [
                    expand: true
                    src: ['**/*.png']
                    cwd: 'less'
                    dest: 'dist/css'
                    filter: 'isFile'
                ]
            js:
                files: [
                    expand: true
                    src: ['**/*.js', '**/*.json']
                    cwd: 'js'
                    dest: 'build'
                    filter: 'isFile'
                ]

        umd:
            jade: {
                options: {
                    src: [
                        'build/jade_tmpl/interactionPage.js'
                        'build/jade_tmpl/moviesPage.js'
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
            compile:
                expand: true
                #flatten: true
                cwd: 'js'
                src: ['**/*.coffee']
                dest: 'build'
                ext: '.js'
                bare: false

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

    grunt.registerTask 'build', ['copy', 'coffee', 'less', 'jade', 'umd', 'browserify:build']
    grunt.registerTask 'test', ['copy', 'coffee', 'less', 'jade', 'umd', 'browserify:test']