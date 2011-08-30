from django.shortcuts import render_to_response
from django.template import RequestContext
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
                'type': 'Point',
                'coordinates': transcript.muni.lat_long.coords,
            },
            'properties': {
                'entity': transcript.muni.name,
                'occurrences': transcript.occurrences,
                'date': str(transcript.date.date()),
            }
        } for transcript in qs if transcript.muni.lat_long is not None]
    }
    
    return HttpResponse(json.dumps(out), mimetype="application/json")
    
def cloud(request):
    
    #call some helper function to get a list of the most frequent words instead of this placeholder
    tags = [{ 'tag': 'django', 'size': 10 },
            { 'tag': 'python', 'size': 8 },
            { 'tag': 'Australia', 'size': 1 },
            { 'tag': 'coffee', 'size': 6 },
            { 'tag': 'pycon', 'size': 3 },
            { 'tag': 'html', 'size': 9 },
            ]

    render_to_response('cloud.html', {'data': tags }, context_instance=RequestContext(request))
