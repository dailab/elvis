import os
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

import unittest
import elvis.distribution

class TestDistributions(unittest.TestCase):
    def test_linear(self):
        dist = elvis.distribution.InterpolatedDistribution.linear([[0, 0], [1, 2], [2, 4], [3, 9]], [0, 3])
        self.assertEqual(dist[0], 0)
        self.assertEqual(dist[0.5], 1)
        self.assertEqual(dist[2.5], 6.5)

        self.assertEqual(dist[-1], 0)
        self.assertEqual(dist[120], 9)
        
        dist = elvis.distribution.EquallySpacedInterpolatedDistribution.linear([[0, 0], [1, 2], [2, 4], [3, 9]], [0, 3])
        self.assertEqual(dist[0], 0)
        self.assertEqual(dist[0.5], 1)
        self.assertEqual(dist[2.5], 6.5)

        self.assertEqual(dist[-1], 0)
        self.assertEqual(dist[120], 9)

if __name__ == '__main__':
    unittest.main()