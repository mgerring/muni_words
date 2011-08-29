"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from scrape_cc import util
from models import *

class DBBuildTest(TestCase):
    def test_build_db(self):
        util.build_db( ['http://houselive.gov/JSON.php?clip_id=5361','http://pueblo.granicus.com/MediaPlayer.php?view_id=4&clip_id=92'] )
        a = Muni.objects.all()
        b = Transcript.objects.all()
        c = a.filter(name="houselive")
        d = b.filter(clip_id="5361")
        self.assertEquals(a.count(), 2)
        self.assertEquals(b.count(), 2)
        self.assertEquals(c.count(), 1)
        self.assertEquals(d.count(), 1)
