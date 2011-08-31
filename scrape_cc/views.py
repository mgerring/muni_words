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
    
    # aggregate munis
    munis = {}
    for transcript in qs:
        if transcript.muni.id not in munis:
            munis[transcript.muni.id] = []
        munis[transcript.muni.id].append(transcript)
    
    # build GeoJSON
    out = {
        'type': 'FeatureCollection',
        'features': [{
            'id': transcript.id,
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': muni[0].muni.lat_long.coords,
            },
            'properties': {
                'entity': muni[0].muni.name,
                'occurrences': sum([transcript.occurrences for transcript in muni]),
            }
        } for muni in munis.values() if muni[0].muni.lat_long is not None]
    }
    
    return HttpResponse(json.dumps(out), mimetype="application/json")
    
def cloud(request):
    from django.db import connection, transaction
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM ts_stat('SELECT text_vector FROM scrape_cc_transcript') ORDER BY nentry DESC, word LIMIT 150;")
    tags = []
    words = cursor.fetchall()
    high = int(words[0][2])
    low = int(words[-1][2])
    step = (high - low) / 10 

    for row in words:
        freq = int(row[2])
        tag_weight = 1
        interval = low
        while freq > interval:
            interval = interval + (step * tag_weight)
            tag_weight = tag_weight + 1

        tags.append({'tag': row[0], 'size': tag_weight })

    #call some helper function to get a list of the most frequent words instead of this placeholder

    return render_to_response('cloud.html', {'data': tags }, context_instance=RequestContext(request))
