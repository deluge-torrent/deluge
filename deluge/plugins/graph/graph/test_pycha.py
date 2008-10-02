#use pycha instead of homegrown graphs?
"""
good :
* pretty easy&sane.

bad :
* docs are sparse.

Make it look like the deluge graph:
#Is it easy to hack in a n'th line color option? --> probably just not documented... ->YEP
*fill is broken? , no opacity. -> pycha needs to be hacked to mimic the current deluge style.
*how to set line-width?
*kbps label on y axis
"""
print "test_pycha"
upload = [66804, 66915, 66974, 67447, 67540, 67318, 67320, 67249, 66659, 66489, 67027, 66914, 66802, 67303, 67654, 67643, 67763, 67528, 67523, 67431, 67214, 66939, 67316, 67020, 66881, 67103, 67377, 67141, 67366, 67492, 67375, 67203, 67056, 67010, 67029, 66741, 66695, 66868, 66805, 66264, 66249, 66317, 66459, 66306, 66681, 66954, 66662, 66278, 65921, 65695, 65681, 65942, 66000, 66140, 66424, 66480, 66257, 66271, 66145, 65854, 65568, 65268, 65112, 65050, 65027, 64676, 64655, 64178, 64386, 63979, 63271, 62746, 62337, 62297, 62496, 62902, 63801, 64121, 62957, 62921, 63051, 62644, 63240, 64107, 63968, 63987, 63644, 63263, 63153, 62999, 62843, 62777, 63101, 63078, 63178, 63, 63, 6, 62, 625, 62254, 61485, 61264, 60937, 60568, 61011, 61109, 60325, 60196, 59640, 59619, 59514, 60813, 60572, 61632, 61689, 63365, 64583, 66396, 67179, 68209, 68295, 67674, 67559, 67195, 66178, 65632, 66124, 66456, 66676, 67183, 67620, 66960, 66347, 65925, 65907, 65896, 66738, 66703, 67060, 67004, 67007, 66329, 65304, 52002, 38969, 25433, 12426, 0, 0]
download = [42926, 43853, 43157, 45470, 44254, 46272, 45083, 47344, 46716, 51963, 50112, 52334, 55525, 57545, 53691, 51637, 49574, 49836, 48295, 49843, 52878, 56014, 56966, 56938, 60065, 60461, 56542, 59526, 58678, 54424, 51862, 55109, 52132, 53783, 51687, 56567, 52182, 50758, 46714, 50511, 48161, 50920, 48694, 50528, 55074, 55420, 55882, 59268, 59958, 57938, 57115, 51424, 51180, 53184, 52879, 51177, 54417, 51097, 47901, 49870, 55865, 61118, 61476, 63498, 58878, 49630, 45975, 45632, 45892, 44855, 49495, 48304, 45829, 42152, 39403, 37574, 32384, 34933, 34901, 33492, 31953, 36271, 33826, 34515, 36408, 41106, 43054, 44110, 40810, 41383, 37267, 35881, 38660, 37525, 34857, 36718, 36842, 34281, 39528, 41854, 42952, 40021, 41722, 41045, 42917, 39287, 38672, 32824, 28765, 22686, 18490, 15714, 15268, 14793, 15305, 16354, 16720, 17502, 17857, 16622, 18447, 19929, 31138, 36965, 36158, 32795, 30445, 21997, 18100, 22491, 27227, 29317, 32436, 35700, 39140, 36258, 33697, 24751, 20354, 8211, 3836, 1560, 834, 2034, 1744, 1637, 1637, 1637, 0, 0]

import sys
import cairo
#import pycha.line
import pycha_line_deluge
from pycha import line as line_03
from pycha.color import hex2rgb
from pycha.chart import Option


#Complete pycha style ;
options = Option(
    axis=Option(
        lineWidth=1.0,
        lineColor='#000000',
        tickSize=3.0,
        labelColor='#666666',
        labelFont='Tahoma',
        labelFontSize=20,
        labelWidth=50.0,
        x=Option(
            hide=True,
            ticks=None,
            tickCount=10,
            tickPrecision=1,
            range=None,
            rotate=None,
            label=None,
        ),
        y=Option(
            hide=False,
            ticks=None,
            tickCount=3,
            tickPrecision=1,
            range=None,
            rotate=None,
            label=None,
        ),
    ),
    background=Option(
        hide=False,
        baseColor=None,
        chartColor='#ffffff',
        lineColor='#f5f5f5',
        lineWidth=1.5,
    ),
    legend=Option(
        opacity=0.8,
        borderColor='#FFFFFF',
        style={},
        hide=False,
        position=Option(top=0, left=800 - 100)
    ),
    padding=Option(
        left=30,
        right=30,
        top=15,
        bottom=15,
    ),
    stroke=Option(
        color='#ffffff',
        hide=False,
        shadow=True,
        width=4
    ),
    fillOpacity=0.5,
    shouldFill=True,
    barWidthFillFraction=0.75,
    xOriginIsZero=True,
    yOriginIsZero=True,
    pieRadius=0.4,
    colorScheme="blue",
    title=None,
    titleFont='Tahoma',
    titleFontSize=20,
)
######


def test_colscheme():
    print pycha.color.generateColorscheme("#6d1d1d", ["one","two"])



def lineChart(output , line, override_options):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 800, 200)

    options["colorScheme"] = {
        'upload':(0,   0,   1.0) ,
        'upload_fill':(0.43,0.43,1.1, 0.5),
        'download': (0.2,  0.5,0.2),
        'download_fill':(0.6 ,1.1 ,   0.6, 1.0)

    }
    options.update(override_options)

    dataSet = (
        ('download',[(i, bps / 1024) for  i, bps  in enumerate(reversed(download)) ] ),
        ('upload',  [(i, bps / 1024) for  i, bps  in enumerate(reversed(upload)) ]   ),


       )


    chart = line.LineChart(surface, options)

    chart.addDataset(dataSet)
    chart.render()

    surface.write_to_png(output)


#---------------------------------------------

#test_colscheme()
lineChart("pycha1.png", pycha_line_deluge, {})
lineChart("pycha_original.png", line_03, Option( shouldFill=False))


