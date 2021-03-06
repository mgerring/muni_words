from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from django.conf import settings

urlpatterns = patterns('scrape_cc.views',
    url(r'^$', direct_to_template, {'template': 'index.html'}, name='index'),
    url(r'^map/(?P<term>\w+)/$', direct_to_template, {'template': 'index.html'}, name='index-with-word'),
    url(r'^about/$', direct_to_template, {'template': 'about.html'}, name='about'),
    url(r'^cloud/$', 'cloud', name='cloud'),
    url(r'^geo.json', 'geo_json', name='geo_json'),
    url(r'^sparkline.json', 'sparkline', name='sparkline')

)

urlpatterns += patterns('',
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
)
