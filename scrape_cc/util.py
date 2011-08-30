import httplib2
import urlparse
import json
import re
from models import *
import datetime
import htmlentitydefs
from django.contrib.gis.geos import Point
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup


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
            try:
                j = json.loads(ts, strict=False)
            except UnicodeDecodeError:
                ts = unicode(ts, errors='ignore')
                j = json.loads(ts, strict=False)
        except:
            j = False
    else:
        j = False
    return j


def strip_html(string):
    return ''.join([e for e in BeautifulSoup(string).recursiveChildGenerator() if isinstance(e, unicode)]).replace('&nbsp;', ' ')

def build_db(domain, clip_id, muni):
    j = granicus_json_scrape(domain, clip_id)
    if j and len(j) > 0 and len(j[0]) > 0:
        
        text = " ".join([x["text"] if x['type'] != "meta" else "" for x in j[0] ])
        titles = " ".join([x["title"] if x['type'] == "meta" else "" for x in j[0] ])

        try:
            final_text = strip_html(BeautifulStoneSoup(text, convertEntities=BeautifulStoneSoup.ALL_ENTITIES).contents[0])
        except:
            final_text = strip_html(text)
        try:
            final_titles = strip_html(BeautifulStoneSoup(titles, convertEntities=BeautifulStoneSoup.ALL_ENTITIES).contents[0])
        except:
            final_titles = strip_html(titles)

        if final_text == " ":
            cc = True
        else:
            cc = False
        
        try:
            t = Transcript.objects.get_or_create(clip_id=clip_id, muni=muni)[0]
            t.text = final_text
            t.titles = final_titles
            t.cc = cc

            t.save()
        except Exception as e:
            print "Couldn't save transcript object - %s" % e

def get_clips():

    munis = Muni.objects.all()
    count = 0
    total_munis = munis.count()
    
    for m in munis:
        print "Processing %s of %s total munis - %s" % (count, total_munis, m.name)

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
                return

            for vid in videos:
                
                if vid['_type'] != 'video':
                    continue
                else:
                    try:
                        build_db(m.host_url, vid['_source']['id'], m )
                    except Exception as e:
                        print "error in build_db for %s - %s - %s" % ( m.host_url, vid['_source']['id'], e)

            print "Processed %s videos" % len(videos)
        else:       
            print "Response not OK"

        count += 1

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
                pt = Point(agency['_source']['location'][0],  agency['_source']['location'][1])
                new_agency.lat_long = pt
            except:
                pass

            new_agency.save()


def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            #character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 15))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            #named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)



