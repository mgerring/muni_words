from django.http import HttpResponse
import json
import re

from scrape_cc import models

TERM_CLEANER = re.compile('[^\w\s]+')
WHITE_SPACE = re.compile('\s+')

def geo_json(request):
    # build query
    
    qs = models.Transcript.objects.all().select_related()
    
    if 'term' in request.GET:
        term = request.GET['term']
        term = TERM_CLEANER.sub('', term).strip()
        term = WHITE_SPACE.sub(' & ', term)
        
        # this directly interpolates terms into strings before sending them to the DB
        # (ack!) but Django doesn't seem to be able to do selects with interpolation,
        # and the above should blank out any non-letters, so should be safe from SQL
        # injection.
        
        qs = qs.extra(
            select = {'occurrences': "ts_count(text_vector, to_tsquery('%s'))" % term},
            where = ["text_vector @@ to_tsquery('%s')" % term]
        )
    
    # build GeoJSON
    out = {
        'type': 'FeatureCollection',
        'features': [{
            'id': transcript.id,
            'type': 'Feature',
            'geometry': {
                
            }
        } for transcript in qs]
    }
    
    return HttpResponse(qs.count())