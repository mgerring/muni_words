import httplib2
import urlparse
import json
import re
from models import *
import datetime


h = httplib2.Http()
today = datetime.datetime.today()
six_months_ago = (today - datetime.timedelta(weeks=24)).strftime('%Y-%m-%dT%H:%M:%S') 

def granicus_json_scrape(domain, clip_id, raw = False):
    """
    Accepts any Granicus url with a 'clip_id' parameter and returns 
    a Python object containing all the JSON found.
    """
    g_url = 'http://%s/JSON.php?clip_id=%s' % ( domain, clip_id)
    response, j = h.request(g_url)
    if response.get('status') == '200':
        try:
            j = json.loads(j, strict=False)
        except ValueError:
            ts = re.sub('([{,]\s+)([a-z]+)(: ")', lambda s: '%s"%s"%s' % (s.groups()[0], s.groups()[1], s.groups()[2]), j).replace("\\", "")
            print g_url
            try:
                j = json.loads(ts, strict=False)
            except UnicodeDecodeError:
                ts = unicode(ts, errors='ignore')
                j = json.loads(ts, strict=False)
        except:
            j = False
    else:
        j = False
    print j
    return j

def build_db(domain, clip_id, muni):
    j = granicus_json_scrape(domain, clip_id)
    if j and len(j) > 0 and len(j[0]) > 0:
        
        text = " ".join([x["text"] if x['type'] != "meta" else "" for x in j[0] ])
        titles = " ".join([x["title"] if x['type'] == "meta" else "" for x in j[0] ])
        if text == " ":
            cc = True
        else:
            cc = False
        
        Transcript.objects.get_or_create(
            text = text,
            titles = titles,
            cc = cc,
            clip_id = clip_id,
            muni = muni
        )

def get_clips():

    munis = Muni.objects.all()

    for m in munis:
        es_filter_data = """{ "size": 1, 
                              "query": {
                                        "term": {
                                                "agency_id": "%s" 
                                                }
                                     }, 
                              "filter": { "range": { 
                                                "datetime": { 
                                                            "from": "%s", 
                                                            "include_lower": true
                                                            }
                                                 }
                                      }
                            }""" % (m.granicus_id, six_months_ago)

        resp, content = h.request("http://govflix.com/api", "POST", body=es_filter_data)

        if resp.get('status') == '200':
            
            total_json = json.loads(content, strict=False)
            total = total_json['hits']['total']
            es_filter_data = '{ "size": %d, "query": {"term": {"agency_id": "%s" }},  "filter": { "range": { "datetime": { "from": "%s", "include_lower": true}}}}' % ( total, m.granicus_id, six_months_ago)

            resp, content = h.request("http://govflix.com/api", "POST", body=es_filter_data)
            m_json = json.loads(content, strict=False)
            try:
                videos = m_json['hits']['hits']
            except:
                print content
                return

            for vid in videos:
                
                if vid['_type'] != 'video':
                    continue
                else:
                    print vid['_source']['datetime']
#                    try:
                    build_db(m.host_url, vid['_source']['id'], m )
 #                   except:
  #                      print "ERROR"
        else:       
            print content

def import_muni():
    
    api_url = "http://govflix.com/api?type=agency&size=1"
    response, text  = h.request(api_url)

    if response.get('status') == '200':
        agencies = json.loads(text, strict=False)
        total_agencies = agencies['hits']['total']
        
        response, text = h.request("http://govflix.com/api?type=agency&size=%s" % total_agencies)
        agencies = json.loads(text, strict=False)

        for agency in agencies['hits']['hits']:

            new_agency = Muni.objects.get_or_create(granicus_id=agency['_id'])[0]
            new_agency.name = agency['_source']['name']
            new_agency.state = agency['_source']['state']
            new_agency.host_url = agency['_source']['host']
            try:
                new_agency.lat = agency['_source']['location'][0]
                new_agency.lng = agency['_source']['location'][1]
            except:
                pass

            new_agency.save()

         








