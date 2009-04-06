# -*- coding: utf-8 -*-
# aboutdialog.py
#
# Copyright (C) 2007 Marcos Pinto ('markybob') <markybob@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
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
# 	Boston, MA  02110-1301, USA.
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
#

#


import pygtk
pygtk.require('2.0')
import gtk
import pkg_resources

import deluge.common
import deluge.ui.gtkui.common as common
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
        self.about.set_copyright(u'Copyright \u00A9 2007-2009 Andrew Resch')
        self.about.set_comments("A peer-to-peer file sharing program\nutilizing the Bittorrent protocol.")
        self.about.set_version(version)
        self.about.set_authors(["Andrew Resch", "",
            "NullUI (replaced by ConsoleUI):", "Sadrul Habib Chowdhury", "", "WebUI:", "Martijn Voncken", "", "ConsoleUI:", "Ido Abramovich", "", "AjaxUI:", "Damien Churchill", "", "libtorrent (www.libtorrent.org):", "Arvid Norberg", "", "Past Developers:", "Zach Tibbitts", "Alon Zakai", "Marcos Pinto", "Alex Dedul"])
        self.about.set_artists(["Andrew Wedderburn", "Andrew Resch"])
        self.about.set_translator_credits("Aaron Wang Shi \nabbigss \nABCdatos \nAbcx \nActam \nAdam \nadaminikisi \nadi_oporanu \nAdrian Goll \nafby \nAhmades \nAhmad Farghal \nAhmad Gharbeia أحمد غربية \nakira \nAki Sivula \nAlan Pepelko \nAlberto \nAlberto Ferrer \nalcatr4z \nAlckO \nAleksej Korgenkov \nAlessio Treglia \nAlexander Ilyashov \nAlexander Matveev \nAlexander Saltykov \nAlexander Taubenkorb \nAlexander Telenga \nAlexander Yurtsev \nAlexandre Martani \nAlexandre Rosenfeld \nAlexandre Sapata Carbonell \nAlexey Osipov \nAlin Claudiu Radut \nallah \nAlSim \nAlvaro Carrillanca P. \nA.Matveev \nAndras Hipsag \nAndrás Kárász \nAndrea Ratto \nAndreas Johansson \nAndreas Str \nAndré F. Oliveira \nAndreiF \nandrewh \nAngel Guzman Maeso \nAníbal Deboni Neto \nanimarval \nAntonio Cono \nantoniojreyes \nAnton Shestakov \nAnton Yakutovich \nantou \nArkadiusz Kalinowski \nArtin \nartir \nAstur \nAthanasios Lefteris \nAthmane MOKRAOUI (ButterflyOfFire) \nAugusta Carla Klug \nAvoledo Marco \naxaard \nAxelRafn \nAxezium \nAyont \nb3rx \nBae Taegil \nBajusz Tamás \nBalaam's Miracle \nBallestein \nBent Ole Fosse \nberto89 \nbigx \nBjorn Inge Berg \nblackbird \nBlackeyed \nblackmx \nBlueSky \nBlutheo \nbmhm \nbob00work \nboenki \nBogdan Bădic-Spătariu \nbonpu \nBoone \nboss01 \nBranislav Jovanović \nbronze \nbrownie \nBrus46 \nbumper \nbutely \nBXCracer \nc0nfidencal \nCan Kaya \nCarlos Alexandro Becker \ncassianoleal \nCédric.h \nCésar Rubén \nchaoswizard \nChen Tao \nchicha \nChien Cheng Wei \nChristian Kopac \nChristian Widell \nChristoffer Brodd-Reijer \nchristooss \nCityAceE \nClopy \nClusty \ncnu \nCommandant \nConstantinos Koniaris \nCoolmax \ncosmix \nCostin Chirvasuta \nCoVaLiDiTy \ncow_2001 \nCrispin Kirchner \ncrom \nCruster \nCybolic \nDan Bishop \nDanek \nDani \nDaniel Demarco \nDaniel Ferreira \nDaniel Frank \nDaniel Holm \nDaniel Høyer Iversen \nDaniel Marynicz \nDaniel Nylander \nDaniel Patriche \nDaniel Schildt \nDaniil Sorokin \nDante Díaz \nDaria Michalska \nDarkenCZ \nDarren \nDaspah \nDavid Eurenius \ndavidhjelm \nDavid Machakhelidze \nDawid Dziurdzia \nDaya Adianto \ndcruz \nDeady \nDereck Wonnacott \nDevgru \nDevid Antonio Filoni \nDevilDogTG \ndi0rz` \nDialecti Valsamou \nDiego Medeiros \nDkzoffy \nDmitrij D. Czarkoff \nDmitriy Geels \nDmitry Olyenyov \nDominik Kozaczko \nDominik Lübben \ndoomster \nDorota Król \nDoyen Philippe \nDread Knight \nDreamSonic \nduan \nDuong Thanh An \nDvoglavaZver \ndwori \ndylansmrjones \nEbuntor \nEdgar Alejandro Jarquin Flores \nEetu \nekerazha \nElias Julkunen \nelparia \nEmberke \nEmiliano Goday Caneda \nEndelWar \neng.essam \nenubuntu \nercangun \nErdal Ronahi \nergin üresin \nEric \nÉric Lassauge \nErlend Finvåg \nErrdil \nethan shalev \nEvgeni Spasov \nezekielnin \nFabian Ordelmans \nFabio Mazanatti \nFábio Nogueira \nFaCuZ \nFelipe Lerena \nFernando Pereira \nfjetland \nFlorian Schäfer \nFoBoS \nFolke \nForce \nfosk \nfragarray \nfreddeg \nFrédéric Perrin \nFredrik Kilegran \nFreeAtMind \nFulvio Ciucci \nGabor Kelemen \nGalatsanos Panagiotis \nGaussian \ngdevitis \nGeorg Brzyk \nGeorge Dumitrescu \nGeorgi Arabadjiev \nGeorg Sieber \nGerd Radecke \nGermán Heusdens \nGianni Vialetto \nGigih Aji Ibrahim \nGiorgio Wicklein \nGiovanni Rapagnani \nGiuseppe \ngl \nglen \ngranjerox \nGreen Fish \ngreentea \nGreyhound \nG. U. \nGuillaume BENOIT \nGuillaume Pelletier \nGustavo Henrique Klug \ngutocarvalho \nGuybrush88 \nHans Rødtang \nHardDisk \nHargas Gábor \nHeitor Thury Barreiros Barbosa \nhelios91940 \nhelix84 \nHelton Rodrigues \nHendrik Luup \nHenrique Ferreiro \nHenry Goury-Laffont \nHezy Amiel \nhidro \nhoball \nhokten \nHolmsss \nhristo.num \nHubert Życiński \nHyo \nIarwain \nibe \nibear \nId2ndR \nIgor Zubarev \nIKON (Ion) \nimen \nIonuț Jula \nIsabelle STEVANT \nIstván Nyitrai \nIvan Petrovic \nIvan Prignano \nIvaSerge \njackmc \nJacks0nxD \nJack Shen \nJacky Yeung \nJacques Stadler \nJanek Thomaschewski \nJan Kaláb \nJan Niklas Hasse \nJasper Groenewegen \nJavi Rodríguez \nJayasimha (ಜಯಸಿಂಹ) \njeannich \nJeff Bailes \nJesse Zilstorff \nJoan Duran \nJoão Santos \nJoar Bagge \nJoe Anderson \nJoel Calado \nJohan Linde \nJohn Garland \nJojan \njollyr0ger \nJonas Bo Grimsgaard \nJonas Granqvist \nJonas Slivka \nJonathan Zeppettini \nJørgen \nJørgen Tellnes \njosé \nJosé Geraldo Gouvêa \nJosé Iván León Islas \nJosé Lou C. \nJose Sun \nJr. \nJukka Kauppinen \nJulián Alarcón \njulietgolf \nJusic \nJustzupi \nKaarel \nKai Thomsen \nKalman Tarnay \nKamil Páral \nKane_F \nkaotiks@gmail.com \nKateikyoushii \nkaxhinaz \nKazuhiro NISHIYAMA \nKerberos \nKeresztes Ákos \nkevintyk \nkiersie \nKimbo^ \nKim Lübbe \nkitzOgen \nKjetil Rydland \nkluon \nkmikz \nKnedlyk \nkoleoptero \nKőrösi Krisztián \nKouta \nKrakatos \nKrešo Kunjas \nkripken \nKristaps \nKristian Øllegaard \nKristoffer Egil Bonarjee \nKrzysztof Janowski \nKrzysztof Zawada \nLarry Wei Liu \nlaughterwym \nLaur Mõtus \nlazka \nleandrud \nlê bình \nLe Coz Florent \nLeo \nliorda \nLKRaider \nLoLo_SaG \nLong Tran \nLorenz \nLow Kian Seong \nLuca Andrea Rossi \nLuca Ferretti \nLucky LIX \nLuis Gomes \nLuis Reis \nŁukasz Wyszyński \nluojie-dune \nmaaark \nMaciej Chojnacki \nMaciej Meller \nMads Peter Rommedahl \nMajor Kong \nMalaki \nmalde \nMalte Lenz \nMantas Kriaučiūnas \nMara Sorella \nMarcin \nMarcin Falkiewicz \nmarcobra \nMarco da Silva \nMarco de Moulin \nMarco Rodrigues \nMarcos \nMarcos Escalier \nMarcos Pinto \nMarcus Ekstrom \nMarek Dębowski \nMário Buči \nMario Munda \nMarius Andersen \nMarius Hudea \nMarius Mihai \nMariusz Cielecki \nMark Krapivner \nmarko-markovic \nMarkus Brummer \nMarkus Sutter \nMartin \nMartin Dybdal \nMartin Iglesias \nMartin Lettner \nMartin Pihl \nMasoud Kalali \nmat02 \nMatej Urbančič \nMathias-K \nMathieu Arès \nMathieu D. (MatToufoutu) \nMathijs \nMatrik \nMatteo Renzulli \nMatteo Settenvini \nMatthew Gadd \nMatthias Benkard \nMatthias Mailänder \nMattias Ohlsson \nMauro de Carvalho \nMax Molchanov \nMe \nMercuryCC \nMert Bozkurt \nMert Dirik \nMFX \nmhietar \nmibtha \nMichael Budde \nMichael Kaliszka \nMichalis Makaronides \nMichał Tokarczyk \nMiguel Pires da Rosa \nMihai Capotă \nMiika Metsälä \nMikael Fernblad \nMike Sierra \nmikhalek \nMilan Prvulović \nMilo Casagrande \nMindaugas \nMiroslav Matejaš \nmisel \nmithras \nMitja Pagon \nM.Kitchen \nMohamed Magdy \nmoonkey \nMrBlonde \nmuczy \nMünir Ekinci \nMustafa Temizel \nmvoncken \nMytonn \nNagyMarton \nneaion \nNeil Lin \nNemo \nNerijus Arlauskas \nNicklas Larsson \nNicolaj Wyke \nNicola Piovesan \nNicolas Sabatier \nNicolas Velin \nNightfall \nNiKoB \nNikolai M. Riabov \nNiko_Thien \nniska \nNithir \nnoisemonkey \nnomemohes \nnosense \nnull \nNuno Estêvão \nNuno Santos \nnxxs \nnyo \nobo \nOjan \nOlav Andreas Lindekleiv \noldbeggar \nOlivier FAURAX \norphe \nosantana \nOsman Tosun \nOssiR \notypoks \nounn \nOz123 \nÖzgür BASKIN \nPablo Carmona A. \nPablo Ledesma \nPablo Navarro Castillo \nPaco Molinero \nPål-Eivind Johnsen \npano \nPaolo Naldini \nParacelsus \nPatryk13_03 \nPatryk Skorupa \nPattogoTehen \nPaul Lange \nPavcio \nPaweł Wysocki \nPedro Brites Moita \nPedro Clemente Pereira Neto \nPekka \"PEXI\" Niemistö \nPenegal \nPenzo \nperdido \nPeter Kotrcka \nPeter Skov \nPeter Van den Bosch \nPetter Eklund \nPetter Viklund \nphatsphere \nPhenomen \nPhilipi \nPhilippides Homer \nphoenix \npidi \nPierre Quillery \nPierre Rudloff \nPierre Slamich \nPietrao \nPiotr Strębski \nPiotr Wicijowski \nPittmann Tamás \nPlaymolas \nPrescott \nPrescott_SK \npronull \nPrzemysław Kulczycki \nPumy \npushpika \nPY \nqubicllj \nr21vo \nRafał Barański \nrainofchaos \nRajbir \nras0ir \nRat \nrd1381 \nRenato \nRene Hennig \nRene Pärts \nRicardo Duarte \nRichard \nRobert Hrovat \nRoberth Sjonøy \nRobert Lundmark \nRobin Jakobsson \nRobin Kåveland \nRodrigo Donado \nRoel Groeneveld \nrohmaru \nRolf Christensen \nRolf Leggewie \nRoni Kantis \nRonmi \nRostislav Raykov \nroyto \nRuiAmaro \nRui Araújo \nRui Moura \nRune Svendsen \nRusna \nRytis \nSabirov Mikhail \nsalseeg \nSami Koskinen \nSamir van de Sand \nSamuel Arroyo Acuña \nSamuel R. C. Vale \nSanel \nSanti \nSanti Martínez Cantelli \nSardan \nSargate Kanogan \nSarmad Jari \nSaša Bodiroža \nsat0shi \nSaulius Pranckevičius \nSavvas Radevic \nSebastian Krauß \nSebastián Porta \nSedir \nSefa Denizoğlu \nsekolands \nSelim Suerkan \nsemsomi \nSergii Golovatiuk \nsetarcos \nSheki \nShironeko \nShlomil \nsilfiriel \nSimone Tolotti \nSimone Vendemia \nsirkubador \nSławomir Więch \nslip \nslyon \nsmoke \nSonja \nspectral \nspin_555 \nspitf1r3 \nSpiziuz \nSpyros Theodoritsis \nSqUe \nSquigly \nsrtck \nStefan Horning \nStefano Maggiolo \nStefano Roberto Soleti \nsteinberger \nStéphane Travostino \nStephan Klein \nSteven De Winter \nStevie \nStian24 \nstylius \nSukarn Maini \nSunjae Park \nSusana Pereira \nszymon siglowy \ntakercena \nTAS \nTaygeto \ntemy4 \ntexxxxxx \nthamood \nThanos Chatziathanassiou \nTharawut Paripaiboon \nTheodoor \nThéophane Anestis \nThor Marius K. Høgås \nTiago Silva \nTiago Sousa \nTikkel \ntim__b \nTim Bordemann \nTim Fuchs \nTim Kornhammar \nTimo \nTimo Jyrinki \nTimothy Babych \nTitkosRejtozo \nTom \nTomas Gustavsson \nTomas Valentukevičius \nTomasz Dominikowski \nTomislav Plavčić \nTom Mannerhagen \nTommy Mikkelsen \nTom Verdaat \nTony Manco \nTor Erling H. Opsahl \nToudi \ntqm_z \nTrapanator \nTribaal \nTriton \nTuniX12 \nTuomo Sipola \nturbojugend_gr \nTurtle.net \ntwilight \ntymmej \nUlrik \nUmarzuki Mochlis \nunikob \nVadim Gusev \nVagi \nValentin Bora \nValmantas Palikša \nVASKITTU \nVassilis Skoullis \nvetal17 \nvicedo \nviki \nvillads hamann \nVincent Garibal \nVincent Ortalda \nvinchi007 \nVinícius de Figueiredo Silva \nVinzenz Vietzke \nvirtoo \nvirtual_spirit \nVitor Caike \nVitor Lamas Gatti \nVladimir Lazic \nVladimir Sharshov \nWanderlust \nWander Nauta \nWard De Ridder \nWebCrusader \nwebdr \nWentao Tang \nwilana \nWilfredo Ernesto Guerrero Campos \nWim Champagne \nWorld Sucks \nXabi Ezpeleta \nXavi de Moner \nXavierToo \nXChesser \nXiaodong Xu \nxyb \nYaron \nYasen Pramatarov \nYesPoX \nYuren Ju \nYves MATHIEU \nzekopeko \nzhuqin \nZissan \nΓιάννης Κατσαμπίρης \nАртём Попов \nМиша \nШаймарданов Максим \n蔡查理")
        self.about.set_wrap_license(True)
        self.about.set_license(_("This program is free software; you can redistribute \
it and/or modify it under the terms of the GNU General Public License as published by \
the Free Software Foundation; either version 3 of the License, or (at your option) any \
later version. This program is distributed in the hope that it will be useful, but \
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS \
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. You \
should have received a copy of the GNU General Public License along with this program; \
if not, see <http://www.gnu.org/licenses>."))
        self.about.set_website("http://deluge-torrent.org")
        self.about.set_website_label("http://deluge-torrent.org")
        self.about.set_icon(common.get_logo(32))
        self.about.set_logo(gtk.gdk.pixbuf_new_from_file(
                                deluge.common.get_pixmap("deluge-about.png")))

    def run(self):
        self.about.show_all()
        self.about.run()
        self.about.destroy()
