# -*- coding: utf-8 -*-
# aboutdialog.py
#
# Copyright (C) 2007 Marcos Pinto ('markybob') <markybob@gmail.com>
# 
# Deluge is free software.
# 
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 2 of the License, or (at your option)
# any later version.
# 
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA    02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.

import pygtk
pygtk.require('2.0')
import gtk
import pkg_resources

import deluge.common
from deluge.ui.client import aclient as client

class AboutDialog:
    def __init__(self):
        # Get the glade file for the about dialog
        def url_hook(dialog, url):
            deluge.common.open_url_in_browser(url)
        gtk.about_dialog_set_url_hook(url_hook)
        self.about = gtk.AboutDialog()
        self.about.set_position(gtk.WIN_POS_CENTER)
        self.about.set_name("Deluge")
        self.about.set_program_name("Deluge")

        # Get the version and revision numbers
        rev = deluge.common.get_revision()
        version = deluge.common.get_version()
        if rev != "":
            version = version + "r" + rev
        self.about.set_copyright(u'Copyright \u00A9 2007-2008 Andrew Resch')
        self.about.set_comments("A peer-to-peer file sharing program\nutilizing the Bittorrent protocol.")
        self.about.set_version(version)
        self.about.set_authors(["Andrew Resch", "Marcos Pinto", 
            "Sadrul Habib Chowdhury", "Martijn Voncken"])
        self.about.set_artists(["Andrew Wedderburn", "Andrew Resch"])
        self.about.set_translator_credits("Aaron Wang Shi\nabbigss\nABCdatos\nAbcx\nAccord Tsai\nAchim Zien\nActam\nAdam\nadaminikisi\nadaminikisi\nadi_oporanu\nAdrian Goll\nAhmades\nAhmad Farghal\nAhmad Gharbeia أحمد غربية\nakira\nAlan Pepelko\nAlberto\nAlberto Ferrer\nalcatr4z\nAleksej Korgenkov\nAlessio Treglia\nAlexander Ilyashov\nAlexander Matveev\nAlexander Taubenkorb\nAlexander Yurtsev\nAlexandre Martani\nAlexandre Rosenfeld\nAlexandre Sapata Carbonell\nAlexey Osipov\nAlin Claudiu Radut\nallah\nAlSim\nAlvaro Carrillanca P.\nA.Matveev\nAndrea Ratto\nAndreas Johansson\nAndreas Str\nAndrea Tarocchi\nandrewh\nAngel Guzman Maeso\nAníbal Deboni Neto\nanimarval\nAntonio Cono\nantoniojreyes\nAnton Shestakov\nAnton Yakutovich\nantou\nАртём Попов\nArkadiusz Kalinowski\nArtin\nartir\nastur\nAugusta Carla Klug\nAvoledo Marco\nAxelRafn \nAxezium\nAyont\nb3rx\nBae Taegil\nBalaam's Miracle\nBallestein\nBalliba\nBent Ole Fosse\nberto89\nbeyonet\nbigx\nBjorn Inge Berg\nblackbird\nBlackeyed\nblackmx\nBlutheo\nbmhm\nbob00work\nboenki\nBoone\nboss01\nBranislav Jovanović\nbronze\nbrownie\nBrus46\nbumper\nbutely\nc0nfidencal\nCan Kaya\ncassianoleal\nCédric.h\nCésar Rubén\nChangHyo Jeong\nchaoswizard\nChen Tao\nchicha\nChien Cheng Wei\nChristian Kopac\nchristooss\nCityAceE\nClusty\ncnu\nCommandant\nCoolmax\nCostin Chirvasuta\ncow_2001\nCrispin Kirchner\ncrom\nCybolic\nDan Bishop\nDanek\ndani\nDaniel Demarco\nDaniel Frank\nDaniel Høyer Iversen\nDaniel Marynicz\nDaniel Nylander\nDaniel Patriche\nDaniel Schildt\nDante Díaz\ndarh00\nDaria Michalska\nDarkenCZ\nDaspah\nDavid Eurenius\ndavidhjelm\nDavid Machakhelidze \nDawid Dziurdzia\ndcruz\nDeady\nDereck Wonnacott\nDevid Antonio Filoni\nDevilDogTG\ndi0rz`\nDiego Medeiros\nDkzoffy\ndmig\nDmitry Olyenyov\nDominik Kozaczko\nDominik Lübben\nDorota Król\nDoyen Philippe\nDread Knight\nDreamSonic\nduan\nDuong Thanh An\nDvoglavaZver\ndwori\ndylansmrjones\nEbuntor\nEdgar Alejandro Jarquin Flores\nEetu\nekerazha\nElias Julkunen\nelparia\nEmiliano Goday Caneda\nEndelWar\nenubuntu\nercangun\nErdal Ronahi \nEric\nÉric Lassauge\nErlend Finvåg\nErrdil\nEvgeni Spasov\nezekielnin\nFabian Ordelmans\nFabio Mazanatti\nFábio Nogueira\nFaCuZ\nFelipe Lerena\nFernando Pereira\nfjetland\nFlorian Schäfer\nFolke\nForce\nfosk\nfragarray\nfreddeg\nFrédéric Perrin\nFredrik Kilegran\nFreeAtMind\nFulvio Ciucci\nGaussian\ngdevitis\nGeorg Brzyk\nGeorge Dumitrescu\nGeorgi Arabadjiev\nGeorg Sieber\nGerd Radecke\nGermán Heusdens\nGianni Vialetto\nGigih Aji Ibrahim\nGiorgio Wicklein\nGiovanni Rapagnani\ngl\nglen\ngranjerox\nGreen Fish\nGreyhound\nguillaume\nGuillaume Pelletier\nGustavo Henrique Klug\ngutocarvalho\nHans-Jørgen Martinus Hansen\nHans Rødtang\nHardDisk\nhasardeur\nHeitor Thury Barreiros Barbosa\nhelios91940\nhelix84\nHelton Rodrigues\nHendrik Luup\nHenrique Ferreiro\nHenry Goury-Laffont\nHezy Amiel\nhidro\nhokten\nHolmsss\nHoly Cheater\nhristo.num\nIarwain\nibe\nibear\nId2ndR\nIgor Zubarev\nimen\nIonuț Jula\nIsabelle STEVANT\nIvan Petrovic\nIvan Prignano\njackmc\nJacks0nxD\nJack Shen\nJacky Yeung\nJacques Stadler\nJanek Thomaschewski\nJan Kaláb\nJan Niklas Hasse\nJasper Groenewegen\nJavi Rodríguez\njayasimha3000 \njeannich\nJeff Bailes\nJesse Zilstorff\nJoan Duran\nJoão Santos\nJoar Bagge\nJochen Schäfer\nJoe Anderson \nJohn Garland\nJojan\njollyr0ger\nJonas Bo Grimsgaard\nJonas Granqvist\nJonathan Zeppettini\nJørgen\nJørgen Tellnes\njosé\nJosé Geraldo Gouvêa\nJosé Iván León Islas\nJosé Lou C.\nJose Sun\nJr.\nJukka Kauppinen\nJulián Alarcón\njulietgolf\nJusic\nJustzupi\nKaarel\nKai Thomsen\nKamil Páral\nKane_F\nkaotiks@gmail.com\nkaxhinaz\nKazuhiro NISHIYAMA\nKerberos\nkevintyk\nkiersie\nKimbo^\nKim Lübbe\nkitzOgen\nKjetil Rydland\nkluon\nkmikz\nKouta\nKrakatos\nKrešo Kunjas\nkripkenstein\nKristaps\nKristian Øllegaard\nKristoffer Egil Bonarjee\nKrzysztof Janowski\nLarry Wei Liu\nlaughterwym\nLaur Mõtus\nlazka\nleandrud\nlê bình\nliorda\nLKRaider\nLoLo_SaG\nLong Tran\nLow Kian Seong\nLuca Ferretti\nLuis Gomes\nLuis Reis\nŁukasz Wyszyński\nmaaark\nMaciej Chojnacki\nMads Peter Rommedahl\nMajor Kong\nmalde\nMara Sorella\nmarazmista\nMarcin\nMarcin Falkiewicz\nmarcobra\nMarco da Silva\nMarco de Moulin\nMarco Rodrigues\nMarcos Escalier\nMarcos Pinto\nMarcus Ekstrom\nMarek Dębowski\nMario César Señoranis\nMario Munda\nMarius Andersen\nMarius Hudea\nMarius Mihai\nMariusz Cielecki\nMark Krapivner\nmarko-markovic\nMarkus Brummer\nMarkus Sutter\nMartin\nMartin Dybdal\nMartin Iglesias\nMartin Lettner\nMartin Pihl\nMasoud Kalali\nmat02\nMatej Urbančič\nMathias-K\nMathijs\nMatrik\nMatteo Ferrabone\nMatteo Renzulli\nMatteo Settenvini\nMatthias Mailänder\nMauro de Carvalho\nMert Bozkurt\nMert Dirik\nmhietar\nmibtha\nMichael Budde\nMichael Kaliszka\nMichał Tokarczyk\nMiguel Pires da Rosa\nMihai Capotă\nMiika Metsälä\nMikael Fernblad\nMike Sierra\nMilan Prvulović\nMilo Casagrande\nMiroslav Matejaš\nmithras\nMitja Pagon\nM.Kitchen\nMohamed Magdy\nmoonkey\nMrBlonde\nMustafa Temizel\nmvoncken\nNeil Lin\nNemo\nNicklas Larsson\nNicolaj Wyke\nNicola Piovesan\nNicolas Velin\nNightfall\nnik\nNikolai M. Riabov\nNiko_Thien\nniska\nnoisemonkey\nnosense\nNuno Estêvão\nNuno Santos\nnxxs\nnyo\nOjan\noldbeggar\nOlivier FAURAX\nOncle Tom\norphe\nosantana\nOsman Tosun\nOssiR\notypoks\nounn\nOz123\nÖzgür BASKIN\nPablo Ledesma\nPablo Navarro Castillo\nPål-Eivind Johnsen\npano\nPaolo Naldini\nParacelsus\nPatryk Skorupa\nPaul Lange\nPavcio\nPaweł Wysocki\nPedro Brites Moita\nPedro Clemente Pereira Neto\nPekka Niemistö\nPenzo\nperdido\nPeter Kotrcka\nPeter Van den Bosch\nPetter Eklund\nPetter Viklund\nphatsphere\nPhenomen\nPhilipi\npidi\nPierre Quillery\nPierre Slamich\nPietrao\nPiotr Strębski\nPiotr Wicijowski\nPrescott\nPrescott_SK\nPrzemysław Kulczycki\nPumy\npushpika\nPY\nqubicllj\nr21vo\nrainofchaos\nRajbir\nras0ir\nRat\nremus\nRenato\nRene Hennig\nRene Pärts\nRicardo Duarte\nRichard\nRobert Hrovat\nRoberth Sjonøy\nRobert Lundmark\nRobin Jakobsson\nRobin Kåveland\nRodrigo Donado\nRoel Groeneveld\nrohmaru\nRolf Christensen\nRolf Leggewie\nRoni Kantis\nRonmi\nRostislav Raykov\nroyto\nRuiAmaro\nRui Araújo\nRui Moura\nRune Svendsen\nRusna\nSabirov Mikhail\nSami Koskinen\nSamir van de Sand\nSamuel R. C. Vale\nsanafrato\nSanel\nSanti\nSanti Martínez Cantelli\nSargate Kanogan\nSarmad Jari\nSaša Bodiroža\nsat0shi\nSavvas Radević\nSebastian Krauß\nSebastián Porta\nSedir\nsekolands\nsemsomi\nsetarcos\nSheki\nShironeko\nShlomil\nsilfiriel\nSimone Tolotti\nSimone Vendemia\nsirkubador\nSławomir Więch\nslyon\nsmoke\nSonja\nspin_555\nSpiziuz\nsrtck\nStefan Horning\nStefano Maggiolo\nStefano Roberto Soleti\nsteinberger\nStéphane Travostino\nStephan Klein\nStevie\nStian24\nstylius\nSukarn Maini\nSunjae Park\nSusana Pereira\nszymon siglowy\nTAS\nTaygeto\ntexxxxxx\nthamood\nTharawut Paripaiboon\nTheodoor\nThéophane Anestis\nThor Marius K. Høgås\nTiago Silva\nTiago Sousa\nTikkel\ntim__b\nTim Bordemann\nTim Fuchs\nTim Kornhammar\nTimo\nTimo Jyrinki\nTom\nTomas Gustavsson\nTomislav Plavčić\nTom Mannerhagen\nTommy Mikkelsen\nTom Verdaat\nTor Erling H. Opsahl\nToudi\ntqm_z\nTrapanator\nTribaal\nTriton \nTuniX12\nTuomo Sipola\nTurtle.net\ntymmej\numarzuki\nunikob\nVadim Gusev\nVagi\nVASKITTU\nvicedo\nviki\nvillads hamann\nVincent Garibal\nVinícius de Figueiredo Silva\nVinzenz Vietzke\nvirtoo\nvirtual_spirit\nVitor Caike\nVitor Lamas Gatti\nVladimir Lazic\nVladimir Sharshov\nWander Nauta\nWard De Ridder\nWebCrusader\nwebdr\nWentao Tang\nWilfredo Ernesto Guerrero Campos\nWorld Sucks\nXabi Ezpeleta\nXavi de Moner\nXavierToo\nXChesser\nXiaodong Xu\nxyb\nYaron\nYasen Pramatarov\nYesPoX\nYuren Ju\nYves MATHIEU\nZanDaTHraX\nzekopeko\nzhuqin\nZissan\n蔡查理")
        self.about.set_wrap_license(True)
        self.about.set_license(_("This program is free software; you can redistribute \
it and/or modify it under the terms of the GNU General Public License as published by \
the Free Software Foundation; either version 2 of the License, or (at your option) any \
later version. This program is distributed in the hope that it will be useful, but \
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS \
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. You \
should have received a copy of the GNU General Public License along with this program; \
if not, see <http://www.gnu.org/licenses>."))
        self.about.set_website("http://deluge-torrent.org")
        self.about.set_website_label("http://deluge-torrent.org")
        self.about.set_icon(deluge.common.get_logo(32))
        self.about.set_logo(gtk.gdk.pixbuf_new_from_file(
                                deluge.common.get_pixmap("deluge-about.png")))
      
    def run(self):
        self.about.show_all()
        self.about.run()
        self.about.destroy()
