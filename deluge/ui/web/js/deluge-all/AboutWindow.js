/*!
 * Deluge.AboutWindow.js
 *
 * Copyright (c) Damien Churchill 2009-2010 <damoxc@gmail.com>
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 */

Ext.namespace('Deluge.about');

/**
 * @class Deluge.about.AboutCreditsWindow
 * @extends Ext.Window
 */
Deluge.about.AboutCreditsWindow = Ext.extend(Ext.Window, {
    id: 'AboutCreditsWindow',
    title: _('Credits'),
    height: 280,
    width: 350,
    iconCls: 'x-deluge-main-panel',
    closeAction: 'hide',
    layout: 'fit',

    initComponent: function() {
        Deluge.about.AboutCreditsWindow.superclass.initComponent.call(this);

        this.add({
            xtype: 'tabpanel',
            activeTab: 0,
            border: false,
            autoHeight: true,
            items: [{
                xtype: 'textarea',
                title: _('Written by'),
                hideLabel: true,
                disable: true,
                value: this.formatText([
                    _('Current Developers:'), 'Andrew Resch', 'Damien Churchill',
                    'John Garland', 'Calum Lind', '', 'libtorrent (libtorrent.org):',
                    'Arvid Norberg', '', _('Past Developers or Contributors:'),
                    'Zach Tibbitts', 'Alon Zakai', 'Marcos Mobley', 'Alex Dedul',
                    'Sadrul Habib Chowdhury', 'Ido Abramovich', 'Martijn Voncken'
                ])
            },{
                xtype: 'textarea',
                title: _('Translated by'),
                hideLabel: true,
                value: this.formatText([
                    'Aaron Wang Shi', 'abbigss', 'ABCdatos', 'Abcx', 'Actam', 'Adam',
                    'adaminikisi', 'adi_oporanu', 'Adrian Goll', 'afby', 'Ahmades',
                    'Ahmad Farghal', 'Ahmad Gharbeia أحمد غربية', 'akira', 'Aki Sivula',
                    'Alan Pepelko', 'Alberto', 'Alberto Ferrer', 'alcatr4z', 'AlckO',
                    'Aleksej Korgenkov', 'Alessio Treglia', 'Alexander Ilyashov',
                    'Alexander Matveev', 'Alexander Saltykov', 'Alexander Taubenkorb',
                    'Alexander Telenga', 'Alexander Yurtsev', 'Alexandre Martani',
                    'Alexandre Rosenfeld', 'Alexandre Sapata Carbonell',
                    'Alexey Osipov', 'Alin Claudiu Radut', 'allah', 'AlSim',
                    'Alvaro Carrillanca P.', 'A.Matveev', 'Andras Hipsag',
                    'András Kárász', 'Andrea Ratto', 'Andreas Johansson', 'Andreas Str',
                    'André F. Oliveira', 'AndreiF', 'andrewh', 'Angel Guzman Maeso',
                    'Aníbal Deboni Neto', 'animarval', 'Antonio Cono', 'antoniojreyes',
                    'Anton Shestakov', 'Anton Yakutovich', 'antou',
                    'Arkadiusz Kalinowski', 'Artin', 'artir', 'Astur',
                    'Athanasios Lefteris', 'Athmane MOKRAOUI (ButterflyOfFire)',
                    'Augusta Carla Klug', 'Avoledo Marco', 'axaard', 'AxelRafn',
                    'Axezium', 'Ayont', 'b3rx', 'Bae Taegil', 'Bajusz Tamás',
                    "Balaam's Miracle", 'Ballestein', 'Bent Ole Fosse', 'berto89',
                    'bigx', 'Bjorn Inge Berg', 'blackbird', 'Blackeyed', 'blackmx',
                    'BlueSky', 'Blutheo', 'bmhm', 'bob00work', 'boenki',
                    'Bogdan Bădic-Spătariu', 'bonpu', 'Boone', 'boss01',
                    'Branislav Jovanović', 'bronze', 'brownie', 'Brus46', 'bumper',
                    'butely', 'BXCracer', 'c0nfidencal', 'Can Kaya',
                    'Carlos Alexandro Becker', 'cassianoleal', 'Cédric.h',
                    'César Rubén', 'chaoswizard', 'Chen Tao', 'chicha',
                    'Chien Cheng Wei', 'Christian Kopac', 'Christian Widell',
                    'Christoffer Brodd-Reijer', 'christooss', 'CityAceE', 'Clopy',
                    'Clusty', 'cnu', 'Commandant', 'Constantinos Koniaris', 'Coolmax',
                    'cosmix', 'Costin Chirvasuta', 'CoVaLiDiTy', 'cow_2001',
                    'Crispin Kirchner', 'crom', 'Cruster', 'Cybolic', 'Dan Bishop',
                    'Danek', 'Dani', 'Daniel Demarco', 'Daniel Ferreira',
                    'Daniel Frank', 'Daniel Holm', 'Daniel Høyer Iversen',
                    'Daniel Marynicz', 'Daniel Nylander', 'Daniel Patriche',
                    'Daniel Schildt', 'Daniil Sorokin', 'Dante Díaz', 'Daria Michalska',
                    'DarkenCZ', 'Darren', 'Daspah', 'David Eurenius', 'davidhjelm',
                    'David Machakhelidze', 'Dawid Dziurdzia', 'Daya Adianto ', 'dcruz',
                    'Deady', 'Dereck Wonnacott', 'Devgru', 'Devid Antonio Filoni',
                    'DevilDogTG', 'di0rz`', 'Dialecti Valsamou', 'Diego Medeiros',
                    'Dkzoffy', 'Dmitrij D. Czarkoff', 'Dmitriy Geels',
                    'Dmitry Olyenyov', 'Dominik Kozaczko', 'Dominik Lübben', 'doomster',
                    'Dorota Król', 'Doyen Philippe', 'Dread Knight', 'DreamSonic',
                    'duan', 'Duong Thanh An', 'DvoglavaZver', 'dwori', 'dylansmrjones',
                    'Ebuntor', 'Edgar Alejandro Jarquin Flores', 'Eetu', 'ekerazha',
                    'Elias Julkunen', 'elparia', 'Emberke', 'Emiliano Goday Caneda',
                    'EndelWar', 'eng.essam', 'enubuntu', 'ercangun', 'Erdal Ronahi',
                    'ergin üresin', 'Eric', 'Éric Lassauge', 'Erlend Finvåg', 'Errdil',
                    'ethan shalev', 'Evgeni Spasov', 'ezekielnin', 'Fabian Ordelmans',
                    'Fabio Mazanatti', 'Fábio Nogueira', 'FaCuZ', 'Felipe Lerena',
                    'Fernando Pereira', 'fjetland', 'Florian Schäfer', 'FoBoS', 'Folke',
                    'Force', 'fosk', 'fragarray', 'freddeg', 'Frédéric Perrin',
                    'Fredrik Kilegran', 'FreeAtMind', 'Fulvio Ciucci', 'Gabor Kelemen',
                    'Galatsanos Panagiotis', 'Gaussian', 'gdevitis', 'Georg Brzyk',
                    'George Dumitrescu', 'Georgi Arabadjiev', 'Georg Sieber',
                    'Gerd Radecke', 'Germán Heusdens', 'Gianni Vialetto',
                    'Gigih Aji Ibrahim', 'Giorgio Wicklein', 'Giovanni Rapagnani',
                    'Giuseppe', 'gl', 'glen', 'granjerox', 'Green Fish', 'greentea',
                    'Greyhound', 'G. U.', 'Guillaume BENOIT', 'Guillaume Pelletier',
                    'Gustavo Henrique Klug', 'gutocarvalho', 'Guybrush88',
                    'Hans Rødtang', 'HardDisk', 'Hargas Gábor',
                    'Heitor Thury Barreiros Barbosa', 'helios91940', 'helix84',
                    'Helton Rodrigues', 'Hendrik Luup', 'Henrique Ferreiro',
                    'Henry Goury-Laffont', 'Hezy Amiel', 'hidro', 'hoball', 'hokten',
                    'Holmsss', 'hristo.num', 'Hubert Życiński', 'Hyo', 'Iarwain', 'ibe',
                    'ibear', 'Id2ndR', 'Igor Zubarev', 'IKON (Ion)', 'imen',
                    'Ionuț Jula', 'Isabelle STEVANT', 'István Nyitrai', 'Ivan Petrovic',
                    'Ivan Prignano', 'IvaSerge', 'jackmc', 'Jacks0nxD', 'Jack Shen',
                    'Jacky Yeung', 'Jacques Stadler', 'Janek Thomaschewski', 'Jan Kaláb',
                    'Jan Niklas Hasse', 'Jasper Groenewegen', 'Javi Rodríguez',
                    'Jayasimha (ಜಯಸಿಂಹ)', 'jeannich', 'Jeff Bailes', 'Jesse Zilstorff',
                    'Joan Duran', 'João Santos', 'Joar Bagge', 'Joe Anderson',
                    'Joel Calado', 'Johan Linde', 'John Garland', 'Jojan', 'jollyr0ger',
                    'Jonas Bo Grimsgaard', 'Jonas Granqvist', 'Jonas Slivka',
                    'Jonathan Zeppettini', 'Jørgen', 'Jørgen Tellnes', 'josé',
                    'José Geraldo Gouvêa', 'José Iván León Islas', 'José Lou C.',
                    'Jose Sun', 'Jr.', 'Jukka Kauppinen', 'Julián Alarcón',
                    'julietgolf', 'Jusic', 'Justzupi', 'Kaarel', 'Kai Thomsen',
                    'Kalman Tarnay', 'Kamil Páral', 'Kane_F', 'kaotiks@gmail.com',
                    'Kateikyoushii', 'kaxhinaz', 'Kazuhiro NISHIYAMA', 'Kerberos',
                    'Keresztes Ákos', 'kevintyk', 'kiersie', 'Kimbo^', 'Kim Lübbe',
                    'kitzOgen', 'Kjetil Rydland', 'kluon', 'kmikz', 'Knedlyk',
                    'koleoptero', 'Kőrösi Krisztián', 'Kouta', 'Krakatos',
                    'Krešo Kunjas', 'kripken', 'Kristaps', 'Kristian Øllegaard',
                    'Kristoffer Egil Bonarjee', 'Krzysztof Janowski',
                    'Krzysztof Zawada', 'Larry Wei Liu', 'laughterwym', 'Laur Mõtus',
                    'lazka', 'leandrud', 'lê bình', 'Le Coz Florent', 'Leo', 'liorda',
                    'LKRaider', 'LoLo_SaG', 'Long Tran', 'Lorenz', 'Low Kian Seong',
                    'Luca Andrea Rossi', 'Luca Ferretti', 'Lucky LIX', 'Luis Gomes',
                    'Luis Reis', 'Łukasz Wyszyński', 'luojie-dune', 'maaark',
                    'Maciej Chojnacki', 'Maciej Meller', 'Mads Peter Rommedahl',
                    'Major Kong', 'Malaki', 'malde', 'Malte Lenz', 'Mantas Kriaučiūnas',
                    'Mara Sorella', 'Marcin', 'Marcin Falkiewicz', 'marcobra',
                    'Marco da Silva', 'Marco de Moulin', 'Marco Rodrigues', 'Marcos',
                    'Marcos Escalier', 'Marcos Mobley', 'Marcus Ekstrom',
                    'Marek Dębowski', 'Mário Buči', 'Mario Munda', 'Marius Andersen',
                    'Marius Hudea', 'Marius Mihai', 'Mariusz Cielecki',
                    'Mark Krapivner', 'marko-markovic', 'Markus Brummer',
                    'Markus Sutter', 'Martin', 'Martin Dybdal', 'Martin Iglesias',
                    'Martin Lettner', 'Martin Pihl', 'Masoud Kalali', 'mat02',
                    'Matej Urbančič', 'Mathias-K', 'Mathieu Arès',
                    'Mathieu D. (MatToufoutu)', 'Mathijs', 'Matrik', 'Matteo Renzulli',
                    'Matteo Settenvini', 'Matthew Gadd', 'Matthias Benkard',
                    'Matthias Mailänder', 'Mattias Ohlsson', 'Mauro de Carvalho',
                    'Max Molchanov', 'Me', 'MercuryCC', 'Mert Bozkurt', 'Mert Dirik',
                    'MFX', 'mhietar', 'mibtha', 'Michael Budde', 'Michael Kaliszka',
                    'Michalis Makaronides', 'Michał Tokarczyk', 'Miguel Pires da Rosa',
                    'Mihai Capotă', 'Miika Metsälä', 'Mikael Fernblad', 'Mike Sierra',
                    'mikhalek', 'Milan Prvulović', 'Milo Casagrande', 'Mindaugas',
                    'Miroslav Matejaš', 'misel', 'mithras', 'Mitja Pagon', 'M.Kitchen',
                    'Mohamed Magdy', 'moonkey', 'MrBlonde', 'muczy', 'Münir Ekinci',
                    'Mustafa Temizel', 'mvoncken', 'Mytonn', 'NagyMarton', 'neaion',
                    'Neil Lin', 'Nemo', 'Nerijus Arlauskas', 'Nicklas Larsson',
                    'Nicolaj Wyke', 'Nicola Piovesan', 'Nicolas Sabatier',
                    'Nicolas Velin', 'Nightfall', 'NiKoB', 'Nikolai M. Riabov',
                    'Niko_Thien', 'niska', 'Nithir', 'noisemonkey', 'nomemohes',
                    'nosense', 'null', 'Nuno Estêvão', 'Nuno Santos', 'nxxs', 'nyo',
                    'obo', 'Ojan', 'Olav Andreas Lindekleiv', 'oldbeggar',
                    'Olivier FAURAX', 'orphe', 'osantana', 'Osman Tosun', 'OssiR',
                    'otypoks', 'ounn', 'Oz123', 'Özgür BASKIN', 'Pablo Carmona A.',
                    'Pablo Ledesma', 'Pablo Navarro Castillo', 'Paco Molinero',
                    'Pål-Eivind Johnsen', 'pano', 'Paolo Naldini', 'Paracelsus',
                    'Patryk13_03', 'Patryk Skorupa', 'PattogoTehen', 'Paul Lange',
                    'Pavcio', 'Paweł Wysocki', 'Pedro Brites Moita',
                    'Pedro Clemente Pereira Neto', 'Pekka "PEXI" Niemistö', 'Penegal',
                    'Penzo', 'perdido', 'Peter Kotrcka', 'Peter Skov',
                    'Peter Van den Bosch', 'Petter Eklund', 'Petter Viklund',
                    'phatsphere', 'Phenomen', 'Philipi', 'Philippides Homer', 'phoenix',
                    'pidi', 'Pierre Quillery', 'Pierre Rudloff', 'Pierre Slamich',
                    'Pietrao', 'Piotr Strębski', 'Piotr Wicijowski', 'Pittmann Tamás',
                    'Playmolas', 'Prescott', 'Prescott_SK', 'pronull',
                    'Przemysław Kulczycki', 'Pumy', 'pushpika', 'PY', 'qubicllj',
                    'r21vo', 'Rafał Barański', 'rainofchaos', 'Rajbir', 'ras0ir', 'Rat',
                    'rd1381', 'Renato', 'Rene Hennig', 'Rene Pärts', 'Ricardo Duarte',
                    'Richard', 'Robert Hrovat', 'Roberth Sjonøy', 'Robert Lundmark',
                    'Robin Jakobsson', 'Robin Kåveland', 'Rodrigo Donado',
                    'Roel Groeneveld', 'rohmaru', 'Rolf Christensen', 'Rolf Leggewie',
                    'Roni Kantis', 'Ronmi', 'Rostislav Raykov', 'royto', 'RuiAmaro',
                    'Rui Araújo', 'Rui Moura', 'Rune Svendsen', 'Rusna', 'Rytis',
                    'Sabirov Mikhail', 'salseeg', 'Sami Koskinen', 'Samir van de Sand',
                    'Samuel Arroyo Acuña', 'Samuel R. C. Vale', 'Sanel', 'Santi',
                    'Santi Martínez Cantelli', 'Sardan', 'Sargate Kanogan',
                    'Sarmad Jari', 'Saša Bodiroža', 'sat0shi', 'Saulius Pranckevičius',
                    'Savvas Radevic', 'Sebastian Krauß', 'Sebastián Porta', 'Sedir',
                    'Sefa Denizoğlu', 'sekolands', 'Selim Suerkan', 'semsomi',
                    'Sergii Golovatiuk', 'setarcos', 'Sheki', 'Shironeko', 'Shlomil',
                    'silfiriel', 'Simone Tolotti', 'Simone Vendemia', 'sirkubador',
                    'Sławomir Więch', 'slip', 'slyon', 'smoke', 'Sonja', 'spectral',
                    'spin_555', 'spitf1r3', 'Spiziuz', 'Spyros Theodoritsis', 'SqUe',
                    'Squigly', 'srtck', 'Stefan Horning', 'Stefano Maggiolo',
                    'Stefano Roberto Soleti', 'steinberger', 'Stéphane Travostino',
                    'Stephan Klein', 'Steven De Winter', 'Stevie', 'Stian24', 'stylius',
                    'Sukarn Maini', 'Sunjae Park', 'Susana Pereira', 'szymon siglowy',
                    'takercena', 'TAS', 'Taygeto', 'temy4', 'texxxxxx', 'thamood',
                    'Thanos Chatziathanassiou', 'Tharawut Paripaiboon', 'Theodoor',
                    'Théophane Anestis', 'Thor Marius K. Høgås', 'Tiago Silva',
                    'Tiago Sousa', 'Tikkel', 'tim__b', 'Tim Bordemann', 'Tim Fuchs',
                    'Tim Kornhammar', 'Timo', 'Timo Jyrinki', 'Timothy Babych',
                    'TitkosRejtozo', 'Tom', 'Tomas Gustavsson', 'Tomas Valentukevičius',
                    'Tomasz Dominikowski', 'Tomislav Plavčić', 'Tom Mannerhagen',
                    'Tommy Mikkelsen', 'Tom Verdaat', 'Tony Manco',
                    'Tor Erling H. Opsahl', 'Toudi', 'tqm_z', 'Trapanator', 'Tribaal',
                    'Triton', 'TuniX12', 'Tuomo Sipola', 'turbojugend_gr', 'Turtle.net',
                    'twilight', 'tymmej', 'Ulrik', 'Umarzuki Mochlis', 'unikob',
                    'Vadim Gusev', 'Vagi', 'Valentin Bora', 'Valmantas Palikša',
                    'VASKITTU', 'Vassilis Skoullis', 'vetal17', 'vicedo', 'viki',
                    'villads hamann', 'Vincent Garibal', 'Vincent Ortalda', 'vinchi007',
                    'Vinícius de Figueiredo Silva', 'Vinzenz Vietzke', 'virtoo',
                    'virtual_spirit', 'Vitor Caike', 'Vitor Lamas Gatti',
                    'Vladimir Lazic', 'Vladimir Sharshov', 'Wanderlust', 'Wander Nauta',
                    'Ward De Ridder', 'WebCrusader', 'webdr', 'Wentao Tang', 'wilana',
                    'Wilfredo Ernesto Guerrero Campos', 'Wim Champagne', 'World Sucks',
                    'Xabi Ezpeleta', 'Xavi de Moner', 'XavierToo', 'XChesser',
                    'Xiaodong Xu', 'xyb', 'Yaron', 'Yasen Pramatarov', 'YesPoX',
                    'Yuren Ju', 'Yves MATHIEU', 'zekopeko', 'zhuqin', 'Zissan',
                    'Γιάννης Κατσαμπίρης', 'Артём Попов', 'Миша', 'Шаймарданов Максим',
                    '蔡查理'
                ])
            },{
                xtype: 'textarea',
                title: _('Artwork by'),
                hideLabel: true,
                value: this.formatText(['Andrew Wedderburn', 'Andrew Resch'])
            }]
        });

        this.addButton(_('Close'), this.onCloseClick, this);
    },

    formatText: function(text_array) {
        var str = '';
        text_array.forEach(function(l) {
            str += l + '\n'
        });
        return str;
    },

    onCloseClick() {
        this.hide();
    }
});

/**
 * @class Deluge.about.AboutLicenseWindow
 * @extends Ext.Window
 */
Deluge.about.AboutLicenseWindow = Ext.extend(Ext.Window, {
    id: 'AboutLicenseWindow',
    title: _('License'),
    iconCls: 'x-deluge-main-panel',
    closeAction: 'hide',

    initComponent: function() {
        Deluge.about.AboutLicenseWindow.superclass.initComponent.call(this);

        this.addButton(_('Close'), this.onCloseClick, this);
    },

    onCloseClick() {
        this.hide();
    }
});

/**
 * @class Deluge.about.AboutWindow
 * @extends Ext.Window
 */
Deluge.about.AboutWindow = Ext.extend(Ext.Window, {
    id: 'AboutWindow',
    title: _('About Deluge'),
    height: 315,
    width: 270,
    iconCls: 'x-deluge-main-panel',
    resizable: false,
    plain: true,
    layout: {
        type: 'vbox',
        align: 'center'
    },
    buttonAlign: 'center',

    initComponent: function() {
        Deluge.about.AboutWindow.superclass.initComponent.call(this);

        this.credits = new Deluge.about.AboutCreditsWindow();
        this.license = new Deluge.about.AboutLicenseWindow();
        this.addEvents({
            'build_ready': true
        });
        this.on('close', function () {
            this.credits.destroy();
            this.license.destroy();
        });

        var version =  deluge.version;

        var comment =
            _('A peer-to-peer file sharing program\nutilizing the BitTorrent protocol.').replace('\n', '<br/>') +
            '<br/><br/>' +
            _('Client:') + ' ' + version + '<br/>';
        deluge.client.web.connected({
            success: function(connected) {
                if (connected) {
                    //deluge.client.web.get_host_info
                    deluge.client.core.get_libtorrent_version({
                        success: function (lt_version) {
                            comment += '<br/>' + _('libtorrent:') + ' ' + lt_version;
                            Ext.getCmp('about_comment').setText(comment, false);
                            this.fireEvent('build_ready');
                        },
                        scope:this
                    });
                }
                else {
                    this.fireEvent('build_ready');
                }
            },
            failure: function(error) {
                    this.fireEvent('build_ready');
            },
            scope: this
        });

        this.add([{
            xtype: 'box',
            style: 'padding-top: 5px',
            height: 80,
            width: 240,
            cls: 'x-deluge-logo',
            hideLabel: true
        }, {
            xtype: 'label',
            style: 'padding-top: 10px; font-weight: bold; font-size: 16px;',
            text: _('Deluge') + ' ' + version
        }, {
            xtype: 'label',
            id: 'about_comment',
            style: 'padding-top: 10px; text-align:center; font-size: 12px;',
            html: comment
        }, {
            xtype: 'label',
            style: 'padding-top: 10px; font-size: 10px;',
            text: _('Copyright 2007-2015 Deluge Team')
        }, {
            xtype: 'label',
            style: 'padding-top: 5px; font-size: 12px;',
            html: '<a href="https://deluge-torrent.org" target="_blank">deluge-torrent.org</a>'
        }]);

        this.addButton(_('Credits'), this.onCreditsClick, this);
        this.addButton(_('License'), this.onLicenseClick, this);
        this.addButton(_('Close'), this.onCloseClick, this);
    },

    show: function() {
        this.on('build_ready', function() {
            Deluge.about.AboutWindow.superclass.show.call(this);
        })
    },
    
    onCreditsClick: function () {
        this.credits.show();
    },

    onLicenseClick: function () {
        this.license.show();
    },

    onCloseClick: function () {
        this.close();
    }
});

Ext.namespace('Deluge');

Deluge.About = function () {
    (new Deluge.about.AboutWindow()).show();
};
