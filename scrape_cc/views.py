from django.shortcuts import render_to_response
from django.template import RequestContext

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



