# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import unittest
from collections import OrderedDict

from comps.cores.mega.dag import DAG


class TestDAG(unittest.TestCase):
    def test_dag(self):
        dag = DAG()
        dag.add_node("a")
        dag.add_node("b")
        dag.add_edge("a", "b")
        dag.add_node("c")
        dag.add_node("d")
        dag.add_edge("a", "d")
        dag.add_edge("b", "c")
        dag.add_edge("c", "d")
        self.assertEqual(dag.topological_sort(), ["a", "b", "c", "d"])
        self.assertEqual(dag.graph, OrderedDict([("a", {"d", "b"}), ("b", {"c"}), ("c", {"d"}), ("d", set())]))
        self.assertEqual(sorted(dag.all_downstreams("a")), ["b", "c", "d"])
        self.assertEqual(dag.size(), 4)
        self.assertEqual(sorted(dag.predecessors("d")), ["a", "c"])
        self.assertEqual(dag.ind_nodes(), ["a"])
        self.assertEqual(dag.all_leaves(), ["d"])
        self.assertEqual(sorted(dag.all_downstreams("a")), ["b", "c", "d"])
        self.assertEqual(sorted(dag.downstream("a")), ["b", "d"])
        self.assertEqual(dag.predecessors("c"), ["b"])

        dag2 = DAG()
        graph_dict = {"a": ["b", "d"], "b": ["c"], "c": ["d"], "d": []}
        dag2.from_dict(graph_dict)
        self.assertEqual(dag.graph, dag2.graph)

        dag2.delete_edge("a", "b")
        self.assertEqual(dag2.graph, OrderedDict([("a", {"d"}), ("b", {"c"}), ("c", {"d"}), ("d", set())]))
        dag2.delete_node("c")
        self.assertEqual(dag2.graph, OrderedDict([("a", {"d"}), ("b", set()), ("d", set())]))


if __name__ == "__main__":
    unittest.main()
