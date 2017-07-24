(function(window){
    "use strict";

    var RightHolders = function (app) {
        this.app = app;
        this.api_rightholders_all = [];
        this.api_rightholders = {};
        this.rightholdersSelectHTML = '';
        this.aliases = {
            'Warner Bros. Entertainment, Inc.': 'WB',
            'ГК «Кармен»': 'Carmen',
            'Новый Диск': 'New_Disk',
            'Sony Pictures': 'Sony',
            'Мистерия Звука': 'MZ',
            'ЦПШ': 'Central_Partnership',
            //'Русский репортаж': 'Russian_Reportage',
            'CD Land Records Ltd': 'CD_Land',
            '100 фильм': '100_Film',
            'Нон-Стоп Продакшн': 'Non-stop_Production',
            'Цифровая лаборатория': 'Digilab',
            'Кинологистика': 'Cinelogistics',
            //'Планета-Информ': '',
            //'Экспонента': 'Exponenta',
            //'Арена': "Arena",
            'ООО «ПРИОР Дистрибьюшн»': 'Prior_Distribution'
        };
    };

    const legalize  = require('../lib/legalize');

    RightHolders.prototype.refresh = function (callback) {
        const wsNapi = this.app.shared.wsNapi;
        if (wsNapi.state === 'authorized') {
            this.app.setMainStatus('Requesting rightholders list...');
            wsNapi.request({'method': 'rightholders_all', 'params': {}}, function (m) {
                console.log('RightHolders.refresh f1');
                this.api_rightholders_all = m.result.ids;
                // Continue requesting rightholders
                this.app.setMainStatus('Requesting rightholders data...');
                wsNapi.request({'method': 'rightholders', 'params': {'ids': this.api_rightholders_all}}, function (m) {
                    console.log('MoviesData.refresh f2');
                    this.api_rightholders = {};
                    this.rightholdersSelectHTML = '';
                    for (var i = 0; i < m.result.length; i++) {
                        // Rebuild from {"id": x, "name": "Warner Bros. Entertainment, Inc."}
                        // to x: {'name': 'Warner Bros. Entertainment, Inc.', 'legacy': 'Warner_Bros_Entertainment_Inc', 'alias': 'WB'}
                        var rhId = m.result[i].id;
                        var rhName = m.result[i].name;
                        var rhAlias, rhLegacy = legalize(rhName);
                        if (rhName in this.aliases) {
                            rhAlias = this.aliases[rhName];
                        } else {
                            rhAlias = rhLegacy;
                        }
                        this.api_rightholders[rhId] = {
                            'name': rhName,
                            'legacy': rhLegacy,
                            'alias': rhAlias
                        };
                        this.rightholdersSelectHTML += '<option value="'+rhId+'">'+rhName+'</option>';
                    }
                    if (typeof(callback) === 'function')
                        callback();
                }.bind(this));
            }.bind(this));
        } else {
            this.app.setMainStatus('Not authorized');
        }
    };
    module.exports = RightHolders;
})(window);
