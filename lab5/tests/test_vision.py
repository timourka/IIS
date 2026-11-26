import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'webots/controllers/picker'))
from vision import detect, project, fuse

class VisionTests(unittest.TestCase):
    def test_red_detection_uses_bgra_and_rejects_blue(self):
        blue=bytes((240,0,0,255)); red=bytes((0,0,220,255))
        self.assertEqual(detect(blue+red*5,3,2,'red'),(1.2,0.6))
    def test_absent_object(self):
        self.assertIsNone(detect(bytes(4*3*2),3,2,'red'))
    def test_invalid_frame(self):
        with self.assertRaises(ValueError): detect(b'',3,2,'red')
    def test_two_views_agree_in_world_coordinates(self):
        a=project((50,39.5),101,80,1.0,(0.3,0,0.6),0.04)
        b=project((50,39.5),101,80,1.0,(0.31,0,0.6),0.04)
        self.assertAlmostEqual(fuse([a,b])[0],0.305)
    def test_reject_inconsistent_views(self):
        with self.assertRaises(ValueError): fuse([(0,0),(0.1,0)])

if __name__=='__main__': unittest.main()
