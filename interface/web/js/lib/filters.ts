(function(document){
    "use strict";

    const $ = require('jquery');
    const fids = {};

    const unaries = ['!', 'INCLUDES' ,'STARTSWITH' ,'ENDSWITH', 'LENGTH', 'DEFINITION'];
    const binaries = ['>', '<', '>=', '<=', '==', '!=', '&&', '||', '^^'];
    const defaultTokens = [
        {
            name: 'Studio',
            values: null,
            filter:    function (rec) { return new Set([rec.rightholder]); },
            condition: function (val) { return ['PATH:rightholder', val, '==']; }
        },
        {
            name: 'Status',
            values: null,
            filter:    function (rec) { return new Set([rec.movie_status]); },
            condition: function (val) { return ['PATH:movie_status', val, '==']; }
        },
        {
            name: 'Video files',
            values: null,
            filter:    function (rec) { return new Set(Object.keys(rec.video_r)); },
            condition: function (val) { return ['PATH:video_r|' + val]; }
        },
        {
            name: 'Audio',
            values: null,
            filter:    function (rec) { return new Set(Object.keys(rec.audio_r)); },
            condition: function (val) { return ['PATH:audio_r|' + val]; }
        },
        {
            name: 'Subtitles',
            values: null,
            filter:    function (rec) { return new Set(Object.keys(rec.subtitles_r)); },
            condition: function (val) { return ['PATH:subtitles_r|' + val]; }
        },
    ];

    const getKeyVal = function (obj, path) {
        let p = path.split('|');
        let v = obj;
        for (let i = 0; i < p.length && v !== undefined; i++) {
            v = v[p[i]];
        }
        return v;
    };

    class Filters {
        constructor (tokens) {
            // throw new Exception('Filters is static class. Don\'t instantiate');
            var fid;
            do {
                fid = 'f_'+Math.floor((Math.random() * 8999) + 1000);
            } while (fid in fids);
            this.fid = fid;
            fids[fid] = this;
            // Fixed conditions
            this.conditions = [
                // First condition is used for token filter
                {
                    'name': 'Token filter',
                    'condition': [ true ]
                }
            ];
            this.conditionIndex = 0;
            // Token filters
            this.tokens = tokens || defaultTokens.slice(0);
        }

        appendFilterTokens (rec) {
            for (var i = 0; i < this.tokens.length; i++) {
                const f = this.tokens[i].filter(rec);
                if (!this.tokens[i].values) {
                    this.tokens[i].values = f;
                } else {
                    // this.tokens[i].values = new Set([...f, ...this.tokens[i].values]);
                    for (let t of f)
                        this.tokens[i].values.add(t);
                }
            }
        }

        updateFilterCheckbox () {
            var html_th='<tr>', html_td='<tr>', t, ft, j, nm, id, i;
            for (i=0; i<this.tokens.length; i++) {
                ft = this.tokens[i];
                ft.vlist = Array.from(ft.values);
                ft.vlist.sort();
                html_th += '<th>'+ft.name+'</th>';
                html_td += '<td style="vertical-align:top" class="checkboxes">';
                for (j=0; j<ft.vlist.length; j++) {
                    t = ft.vlist[j];
                    nm = this.fid+'_'+ft.name;
                    id = nm+'_'+j;
                    html_td += '<div><input type="checkbox" id="'+id+'" class="tri-state-checkbox '+this.fid+'" name="'+nm+'" value="'+j+'" fval="'+t+'" /><label for="'+id+'">'+t+'</label></div>';
                }
                html_td += '</td>';
            }
            html_th += '</tr>';
            html_td += '</tr>';

            document.getElementById('filters').innerHTML = html_th + html_td;
            var cbs = document.getElementsByClassName(this.fid);

            const ff = function () { return Filters.setFilterFromCheckbox(this); }.bind(this);
            for (i=0; i<cbs.length; i++) {
                cbs[i].onclick = function (e) {
                    var cb = e.currentTarget;
                    if (cb.readOnly)
                        cb.checked=cb.readOnly = false;
                    else if (!cb.checked)
                        cb.readOnly = cb.indeterminate = true;
                };
                cbs[i].onchange = ff;
            }
        }
    }

    Filters.setFilterFromCheckbox = function(filter) {
        var ftcount = 0;
        var condition = [];
        var ft, nm, i;
        for (i=0; i<filter.tokens.length; i++) {
            ft = filter.tokens[i];
            nm = filter.fid+'_'+ft.name;
            var cbs = document.getElementsByName(nm);
            // Scan checkboxes, and if there is any checked (but not all), build filter
            var build = false;
            var allchecked = true;
            for (const j in cbs) {
                if (cbs[j].checked || cbs[j].indeterminate) {
                    build = true;
                    if (!allchecked)
                        break;
                } else {
                    allchecked = false;
                    if (build)
                        break;
                }
            }
            if (allchecked) {
                build = false;
            }
            var tc = 0;
            var nc = 0;
            var negc = [];
            if (build) {
                ftcount++;
                // build condition
                for (const j in cbs) {
                    if (cbs[j].indeterminate) {
                        negc = negc.concat(ft.condition(cbs[j].attributes.fval.value));
                        nc++;
                    } else if (cbs[j].checked) {
                        condition = condition.concat(ft.condition(cbs[j].attributes.fval.value));
                        tc++;
                    }
                }
                if (nc > 0)
                {
                    while (nc > 1) {
                        negc.push('||');
                        nc--;
                    }
                    negc.push('!');
                    if (tc > 0)
                    {
                        negc.push('&&');
                    }
                }
                while (tc > 1) {
                    condition.push('||');
                    tc--;
                }
                condition = condition.concat(negc);
            }
        }
        if (ftcount === 0)
        {
            condition.push(true);
        } else while (ftcount > 1) {
            condition.push('&&');
            ftcount--;
        }
        filter.conditions[0].condition = condition;
        document.getElementById('custom-filter').innerHTML = condition.join(' ');
    };

    // Filters.appendFiltersTokens = function (rec) {
    //     for (const fid in Filters.fids) {
    //         const cflt = Filters.fids[fid];
    //         for (var i=0; i<cflt.tokens.length; i++) {
    //             cflt.tokens[i].values = cflt.tokens[i].filter(rec);
    //         }
    //     }
    // };

    // Filters.updateFiltersCheckboxes = function () {
    //     var html_th='<tr>', html_td='<tr>', t, ft, j, nm, id, i;
    //     for (const fid in Filters.fids) {
    //         const cflt = Filters.fids[fid];
    //         for (i=0; i<cflt.tokens.length; i++) {
    //             ft = cflt.tokens[i];
    //             ft.vlist = Array.from(ft.values);
    //             ft.vlist.sort();
    //             html_th += '<th>'+ft.name+'</th>';
    //             html_td += '<td style="vertical-align:top" class="checkboxes">';
    //             for (j=0; j<ft.vlist.length; j++) {
    //                 t = ft.vlist[j];
    //                 nm = cflt.fid+'_'+ft.name;
    //                 id = nm+'_'+j;
    //                 html_td += '<input type="checkbox" id="'+id+'" class="tri-state-checkbox '+cflt.fid+'" name="'+nm+'" value="'+j+'" fval="'+t+'" /><label for="'+id+'">'+t+'</label><br/>';
    //             }
    //             html_td += '</td>';
    //         }
    //         html_th += '</tr>';
    //         html_td += '</tr>';

    //         document.getElementById('filters').innerHTML = html_th + html_td;
    //         var cbs = document.getElementsByClassName(cflt.fid);

    //         for (i=0; i<cbs.length; i++) {
    //             cbs[i].onclick = function (e) {
    //                 var cb = e.currentTarget;
    //                 if (cb.readOnly)
    //                     cb.checked=cb.readOnly = false;
    //                 else if (!cb.checked)
    //                     cb.readOnly = cb.indeterminate = true;
    //             };
    //             cbs[i].onchange = cflt.setFilterFromCheckbox;
    //         }
    //     }
    // };

    // Filters.filterConditionIndex = 0;

    // Filters.filterConditions = [
    //     {
    //         'name': 'Selection filter',
    //         'condition': [
    //             true
    //         ]
    //     },
    //     {
    //         'name': 'Ayyo',
    //         'condition': [
    //             'PATH:rightholder', 'Ayyo', '=='
    //         ]
    //     },
    //     {
    //         'name': 'SD/HD trailers',
    //         'condition': [
    //             'PATH:video_r|trailer_files@mp4@sd', '@R_SD', 'INCLUDES', '!', ['PATH:video_r|trailer_files@mp4@sd', 'DEFINITION', 'HD', '=='], '&&'
    //         ]
    //     },
    //     {
    //         'name': 'HD desync',
    //         'condition': [
    //             'PATH:video_r|movie_files@playready@hd', '!', 'PATH:video_r|movie_files@playready_offline@hd', '!', '!='
    //         ]
    //     },
    //     {
    //         'name': 'dtr HD vs PR HD',
    //         'condition': [
    //             'PATH:video_r|movie_files@playready@ss@hd', '!', 'PATH:video_r|movie_files@playready_offline@file@hd', '&&'
    //         ]
    //     },
    //     {
    //         'name': 'HD dash & UHD dash',
    //         'condition': [
    //             'PATH:movie_status', 'public', '==', 'PATH:video_r|movie_files@playready@dash@hd', 'PATH:video_r|movie_files@playready@dash@uhd', '&&', '&&'
    //         ]
    //     }
    // ];


    var gcc_rec = null;
    const compute_recursive = function(c) {
        var a, b;
        if (typeof(c) === 'boolean')
            return c;
        if (typeof(c) === 'object') {
            a = compute_recursive(c.args[0]);
            switch (c.op) {
                case '>': {
                    b = compute_recursive(c.args[1]);
                    return(a > b);
                }
                case '<': {
                    b = compute_recursive(c.args[1]);
                    return(a < b);
                }
                case '>=': {
                    b = compute_recursive(c.args[1]);
                    return(a >= b);
                }
                case '<=': {
                    b = compute_recursive(c.args[1]);
                    return(a <= b);
                }
                case '==': {
                    b = compute_recursive(c.args[1]);
                    return(a === b);
                }
                case '!=': {
                    b = compute_recursive(c.args[1]);
                    return(a !== b);
                }
                case '&&': {
                    if (!a)
                    {
                        console.log('Skip testing operand '+b);
                        return(false);
                    }
                    b = compute_recursive(c.args[1]);
                    return(a && b);
                }
                case '||': {
                    if (a)
                    {
                        console.log('Skip testing operand '+b);
                        return(true);
                    }
                    b = compute_recursive(c.args[1]);
                    return(a || b);
                }
                case '^^': {
                    b = compute_recursive(c.args[1]);
                    return((a&&b)||(!(a||b))?false:true);
                }
                case '!': {

                    return(!a);
                }
                case 'LENGTH': {

                    return(a.length);
                }
                case 'INCLUDES': {
                    b = compute_recursive(c.args[1]);
                    if (typeof(a) !== 'string' || typeof(b) !== 'string')
                        return(false);
                    return(b.includes(a));
                }
                case 'STARTSWITH': {
                    b = compute_recursive(c.args[1]);
                    if (typeof(a) !== 'string' || typeof(b) !== 'string')
                        return(false);
                    return(b.startsWith(a));
                }
                case 'ENDSWITH': {
                    b = compute_recursive(c.args[1]);
                    if (typeof(a) !== 'string' || typeof(b) !== 'string')
                        return(false);
                    return(b.endsWith(a));
                }
                case 'DEFINITION': {
                    // Create video element
                    if (typeof(a) !== 'string')
                    {
                        return(false);
                    }
                    if (definitions[a] !== undefined)
                    {
                        return(definitions[a]);
                    }
                    defQueue.push(a);
                    getDefActive = true;
                    return(true);
                }
                default:
                    return(a);
            }
        }
        if (c.startsWith('PATH:')) {
            var v = getKeyVal(gcc_rec, c.substring(5));
            if (typeof(v) === 'undefined') {
                v = false;
                //console.log('Undef');
            }
            return(v);
        }
        return(c);
    };

    Filters.checkCondition = function (rec, cond) {
        // condition has records of these types:
        // string
        // link         PATH:keys|to|find|the|value|in|rec
        //              in this example proc will try to get a value from rec.keys.to.find.the.value.in.rec
        // operation    unary, bool result: ! INCLUDES STARTSWITH ENDSWITH
        //              unary, integer result: LENGTH
        //              unary, string result: DEFINITION
        //              binary, bool result: > < >= <= == != && || ^^

        var result=[], a=0, b=0;
        for (var i = 0; i < cond.length; i++) {
            if (typeof(cond[i]) !== 'string') {
                result.push(cond[i]);
            } else {
                if (unaries.indexOf(cond[i]) !== -1) {
                    a = result.pop();
                    result.push({'op': cond[i], 'args': [a]});
                } else if (binaries.indexOf(cond[i]) !== -1) {
                    a = result.pop();
                    b = result.pop();
                    result.push({'op': cond[i], 'args': [b, a]});   // Keep operands order
                } else {
                    result.push(cond[i]);
                }
            }
        }
        // The result must be an array with length == 1, containing object or bool

        if (result.length !== 1) {
            console.log('Error: check condition ' + cond);
            return false;
        }

        gcc_rec = rec;
        return compute_recursive(result[0]);
    };


    // Filters.filterTokens = [
    //     {
    //         'name': 'Studio',
    //         'values': {},
    //         'filter': function (rec) {
    //             var res = {};
    //             res[rec.rightholder] = 1;
    //             return res;
    //         },
    //         'condition': function (val) { return ['PATH:rightholder', val, '==']; }
    //     },
    //     {
    //         'name': 'Status',
    //         'values': {},
    //         'filter': function (rec) {
    //             var res = {};
    //             res[rec.movie_status] = 1;
    //             return res;
    //         },
    //         'condition': function (val) { return ['PATH:movie_status', val, '==']; }
    //     },
    //     {
    //         'name': 'Video files',
    //         'values': {},
    //         'filter': function (rec) {
    //             var res = {};
    //             for (var token in rec.video_r) {
    //                 res[token] = 1;
    //             }
    //             return res;
    //         },
    //         'condition': function (val) { return ['PATH:video_r|' + val]; }
    //     },
    //     {
    //         'name': 'Audio',
    //         'values': {},
    //         'filter': function (rec) {
    //             var res = {};
    //             for (var token in rec.audio_r) {
    //                 res[token] = 1;
    //             }
    //             return res;
    //         },
    //         'condition': function (val) { return ['PATH:audio_r|' + val]; }
    //     },
    //     {
    //         'name': 'Subtitles',
    //         'values': {},
    //         'filter': function (rec) {
    //             var res = {};
    //             for (var token in rec.subtitles_r) {
    //                 res[token] = 1;
    //             }
    //             return res;
    //         },
    //         'condition': function (val) { return ['PATH:subtitles_r|' + val]; }
    //     },
    // ];


    // Filters.appendFilterTokens = function (rec) {
    //     for (var i in Filters.filterTokens) {
    //         var res = Filters.filterTokens[i].filter(rec);
    //         for (var k in res) {
    //             Filters.filterTokens[i].values[k] = 1;
    //         }
    //     }
    // };





    module.exports = Filters;

})(document);