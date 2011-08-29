#rom django.db import models
from django.contrib.gis.db import models

# Create your models here.

class Muni(models.Model):
    name        = models.CharField(max_length=100)
    full_name   = models.CharField(max_length=100, null=True)
    lat_long    = models.PointField(null=True)
    state       = models.CharField(max_length=2, null=True)
    host_url    = models.CharField(max_length=200, null=True)
    granicus_id = models.IntegerField()


class Transcript(models.Model):
    text    = models.TextField(null=True) #this will probably be the closed captions if they exist
    titles  = models.TextField(null=True) #these are the titles on the minutes if found
    cc      = models.BooleanField() #Whether or not we found closed captioning data
    clip_id = models.CharField(max_length=100)
    muni    = models.ForeignKey(Muni)
