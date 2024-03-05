import unittest
from transcripttotext import DeUm

class TestDeUm(unittest.TestCase):

    def test_upper(self):
        self.assertEqual(DeUm('Um ha', ['um']), 'Ha')
        self.assertEqual(DeUm('Ho um hum', ['um']), 'Ho hum')
        self.assertEqual(DeUm('Ho, um, hum', ['um']), 'Ho, hum')
        self.assertEqual(DeUm('Ho, um, um, hum', ['um']), 'Ho, hum')

        self.assertEqual(DeUm('knowledge. Um, yeah, ', ['um']), 'knowledge. Yeah, ')
        self.assertEqual(DeUm('Um, that, that\'s a good question', ['um']), 'That, that\'s a good question')
        self.assertEqual(DeUm('Um, that, that\'s a good question', ['um']), 'That, that\'s a good question')
        self.assertEqual(DeUm('So yeah, Um so, one of the', ['um']), 'So yeah, so, one of the')

        self.assertEqual(DeUm('Um, and I think I\'m not sure, uh, we could ask legal um, practitioners', ['um', 'uh']), 'And I think I\'m not sure, we could ask legal practitioners')

        self.assertEqual(DeUm('Um er um er ha', ['um', 'er']), 'Ha')

if __name__ == '__main__':
    unittest.main()
