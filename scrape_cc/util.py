import httplib2
import urlparse
import json
import re
from models import *


h = httplib2.Http()

def granicus_json_scrape(url, raw = False):
    """
    Accepts any Granicus url with a 'clip_id' parameter and returns 
    a Python object containing all the JSON found.
    """
    u = urlparse.urlparse(url)
    r = {
        'muni'      : u.netloc.split('.')[0],
        'clip_id'   : urlparse.parse_qs(u.query).get('clip_id',[''])[0]
    }
    response, j = h.request('http://%s/JSON.php?clip_id=%s'%( u.netloc, r['clip_id'] ))
    if response.get('status') == '200':
        try:
            j = json.loads(j)
        except ValueError:
            ts = re.sub('([{,]\s+)([a-z]+)(: ")', lambda s: '%s"%s"%s' % (s.groups()[0], s.groups()[1], s.groups()[2]), j).replace("\\", "")
            print ts
            j = json.loads(ts, strict=False)
        except:
            j = False
    else:
        j = False
    r['response'] = j
    return r

def build_db(urls):
    for url in urls:
        j = granicus_json_scrape(url)
        muni = None
        if j:
            if muni == None or muni.name != j['muni']:
                muni, created = Muni.objects.get_or_create(name=j['muni'])
            
            text = " ".join([x["text"] if x['type'] != "meta" else "" for x in j['response'][0] ])
            titles = " ".join([x["title"] if x['type'] == "meta" else "" for x in j["response"][0] ])
            if text == " ":
                cc = True
            else:
                cc = False
            
            Transcript.objects.create(
                text = text,
                titles = titles,
                cc = cc,
                clip_id = j.get('clip_id'),
                muni = muni
            )

def get_urls():
    """
    Didn't have time to implement this so I'm providing psuedocode

    x = get http://www.granicus.com/Clients/Client-List.aspx
    y = find all A tags inside TDs
    z = []
    for y:
        find all links on page resembling:
        <a href="javascript:void(0);" onclick="window.open('http://addison.granicus.com/MediaPlayer.php?view_id=2&amp;clip_id=2581','player','toolbar=no,directories=no,status=yes,scrollbars=no,resizable=yes,menubar=no,width=800,height=600')">Video</a>
        z.append({"url":the url})
    build_db(z)
    You don't need to normalize the link because granicus_json_scrape knows what we're looking for, but I guess you could.
    """
    pass
