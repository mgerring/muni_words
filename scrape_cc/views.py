from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
import json
import re
from scrape_cc import models

from django.db.models import Sum

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
    
    occurrences = {}
    for muni in munis.keys():
        occurrences[muni] = sum([transcript.occurrences for transcript in munis[muni]])
    
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
                'entity_id': muni[0].muni.id,
                'occurrences': occurrences[muni[0].muni.id],
            }
        } for muni in sorted(munis.values(), key=lambda m: occurrences[m[0].muni.id], reverse=True) if muni[0].muni.lat_long is not None]
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

def sparkline(request):
    if 'term' not in request.GET:
        return HttpResponse('Term is required.', status=400)
    
    term = request.GET['term']
    term = TERM_CLEANER.sub('', term).strip()
    term = WHITE_SPACE.sub(' & ', term)
    
    # same icky interpolation as above
    
    select = "date_trunc('week', date) as week, sum(ts_count(text_vector, to_tsquery('%s')))" % term
    condition = "text_vector @@ to_tsquery('%s')" % term
    
    if 'muni' in request.GET:
        try:
            muni = int(request.GET['muni'])
            condition = condition + (" and muni_id = %d" % muni)
        except:
            pass
    
    from django.db import connection
    
    statement = "select %s from scrape_cc_transcript where %s group by week order by week" % (select, condition)
    
    data = []
    cursor = connection.cursor()
    cursor.execute(statement)
    for row in cursor:
        data.append(row[1])
    
    dmax = max(data)
    dmin = min(data)
    
    # scale to 0-100 if it won't cause a division by zero, otherwise set everything to 50
    if dmax - dmin > 0:
        out = [round(100 * (float(x - dmin) / float(dmax - dmin))) for x in data]
    else:
        out = [50 for x in data]
    
    return HttpResponse(json.dumps(out), mimetype="application/json")
    
    