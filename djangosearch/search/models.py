from django.db import models

# Create your models here.


class Search(models.Model):
    date = models.CharField(max_length=32, blank=True, null=True, default=None)
    links = models.CharField(max_length=2048, blank=True, null=True, default=None)
    language = models.CharField(max_length=16, blank=True, null=True, default=None)
    title = models.TextField(blank=True, null=True, default=None)
    h1 = models.TextField(blank=True, null=True, default=None)
    h2 = models.TextField(blank=True, null=True, default=None)
    h3 = models.TextField(blank=True, null=True, default=None)
    h4 = models.TextField(blank=True, null=True, default=None)
    h5 = models.TextField(blank=True, null=True, default=None)
    h6 = models.TextField(blank=True, null=True, default=None)

    def __str__(self):
        return self.title
