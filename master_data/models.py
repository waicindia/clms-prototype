from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Group

# Create your models here.
class BaseContent(models.Model):
    ACTIVE_CHOICES = ((0, 'No'), (2, 'Yes'),) 
    active = models.PositiveIntegerField(choices=ACTIVE_CHOICES, default=2,db_index=True)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Centre(BaseContent):
    name = models.CharField(max_length=150, blank=False, null=False)
    code = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Centre"

    def __str__(self):
        return self.name    


class State(BaseContent):
    name = models.CharField(max_length=150, blank=False, null=False)
    code =  models.CharField(max_length=50, blank=True, null=True)
    centre = models.ForeignKey(Centre, on_delete=models.CASCADE, blank=False, null=False)

    class Meta:
        verbose_name_plural = "State/UTs"

    def __str__(self):
        return self.name    


class District(BaseContent):
    name = models.CharField(max_length=150, blank=False, null=False)
    code = models.CharField(max_length=50, blank=True, null=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE, blank=False, null=False)

    class Meta:
        verbose_name_plural = "District"

    def __str__(self):
        return self.name    


class ShelterHome(BaseContent):
    name = models.CharField(max_length=150, blank=False, null=False)
    code = models.CharField(max_length=50, blank=True, null=True)
    district = models.ForeignKey(District, on_delete=models.CASCADE, blank=False, null=False)
    address = models.TextField(blank=True, null=True)
    latitude = models.CharField(max_length=100, blank=True, null=True)
    longitude = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
    	verbose_name_plural = "Shelter Homes"

    def __str__(self):
        return self.name    


class Relationship(BaseContent):
    name = models.CharField(max_length=150, blank=False, null=False)

    class Meta:
        verbose_name_plural = "Relationship"

    def __str__(self):
        return self.name    


class ChildClassification(BaseContent):
    name = models.CharField(max_length=150, blank=False, null=False)
    use_for_flagging = models.BooleanField(default=False)

    class Meta:
    	verbose_name_plural = "Child Classification"

    def __str__(self):
        return self.name


class UserLocationRelation(BaseContent):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, null=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=False, null=False)
    location_hierarchy_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    location_id = models.PositiveIntegerField()

    class Meta:
        verbose_name_plural = "User Location Relation"

    def __str__(self):
        return self.user.username


class Config(BaseContent):
    code = models.CharField(max_length=150)
    value = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Config"

    def __str__(self):
        return self.code


class ChartMeta(BaseContent):
    chart_type = models.IntegerField(blank=True, null=True, help_text="1=Column Chart, 2=Pie Chart, 3=Table Chart")
    chart_name = models.CharField(max_length=500, blank=True, null=True)
    chart_title = models.CharField(max_length=500, blank=True, null=True)
    vertical_axis_title = models.CharField(max_length=200, blank=True, null=True)
    horizontal_axis_title = models.CharField(max_length=200, blank=True, null=True)
    chart_note = models.TextField(blank=True, null=True)
    chart_tooltip = models.TextField(blank=True, null=True)


    class Meta:
        verbose_name_plural = "Chart Meta"

    def __str__(self):
        return self.chart_name