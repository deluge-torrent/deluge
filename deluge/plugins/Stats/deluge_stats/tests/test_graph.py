# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.

from unittest.mock import Mock

from deluge_stats.graph import Graph


def make_graph():
    graph = Graph()
    graph.add_stat("rate", label="Rate", color=(1.0, 0.0, 0.0))
    graph.set_left_axis(formatter=str, min=1)
    graph.set_stats(
        {
            "_last_update": 1,
            "_length": 3,
            "_update_interval": 1,
            "rate": [1, 2, 3],
        }
    )
    return graph


def test_legend_is_drawn_by_default():
    graph = make_graph()
    graph.draw_legend = Mock()

    graph.draw(400, 200)

    graph.draw_legend.assert_called_once()
    assert graph.stat_info["rate"]["color"] == (1.0, 0.0, 0.0)


def test_legend_can_be_hidden():
    graph = make_graph()
    graph.show_legend = False
    graph.draw_legend = Mock()

    graph.draw(400, 200)

    graph.draw_legend.assert_not_called()
