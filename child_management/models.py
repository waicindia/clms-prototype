from django.db import models
from master_data.models import *
from django.contrib.auth.models import User


# Create your models here.
class Child(BaseContent):
    case_number = models.CharField(max_length=150, blank=False, null=False, unique =True)
    first_name = models.CharField(max_length=150, blank=False, null=False)
    middle_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    dob = models.DateField(blank=False, null=False)
    sex = models.IntegerField(blank=False,null=False,choices=((1,'Male'), (2,'Female'),(3,'Transgender'),(4,'Inter-sex'),(5,'Other')))
    aadhaar_number = models.CharField(max_length=150, blank=True, null=True, unique =True)
    cwc_started_the_process_of_declaring = models.DateField(blank=True, null=True)
    cwc_order_number = models.CharField(max_length=150, blank=True, null=True)
    child_classification = models.ManyToManyField(ChildClassification,blank=False)
    date_declaring_child_free_for_adoption = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='child/', blank=True, null=True)

    class Meta:
        verbose_name_plural = "Child"

    def __str__(self):
        return self.case_number +" - "+ (self.first_name or '') +" "+ (self.middle_name or '') +" "+ (self.last_name or '')


class Guardian(BaseContent):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, blank=False, null=False)
    name = models.CharField(max_length=150, blank=False, null=False)
    relationship = models.ForeignKey(Relationship, on_delete=models.CASCADE, blank=False, null=False)
    address = models.TextField(blank=False, null=False)
    contact_number = models.CharField(max_length=150, blank=False, null=False)
    image = models.ImageField(upload_to='guardian/', blank=True, null=True)

    class Meta:
        verbose_name_plural = "Guardian"

    def __str__(self):
        return (self.child.case_number or '') +" - "+ self.name


class ChildShelterHomeRelation(BaseContent):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, blank=False, null=False,verbose_name='Case number')
    shelter_home = models.ForeignKey(ShelterHome, on_delete=models.CASCADE, blank=False, null=False)
    admission_number =  models.CharField(max_length=150, blank=True, null=True)
    date_of_admission = models.DateField(blank=True, null=True)
    date_of_exit = models.DateField(blank=True, null=True)

    class Meta:
    	verbose_name_plural = "Child with Shelter Home Relation"

    def __str__(self):
        return self.child.case_number     


class FamilyVisit(BaseContent):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, blank=False, null=False)
    guardian = models.ForeignKey(Guardian, on_delete=models.CASCADE, blank=False, null=False)
    date_of_visit = models.DateField(blank=False, null=False)

    class Meta:
    	verbose_name_plural = "Family Visit Tracking"

    def __str__(self):
        return self.child.case_number


class ChildFlaggedHistory(BaseContent):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, blank=False, null=False)
    flagged_date = models.DateField(blank=False, null=False)
    reason_for_flagging = models.TextField(blank=False, null=False)
    flagged_status = models.IntegerField(blank=True,null=True,choices=((1,'Child recommended for adoption enquiry'), (2,'Legally free for adoption'), (3, 'Not applicable')),default=0)

    class Meta:
        verbose_name_plural = "Child Flagged History"

    def __str__(self):
        return self.child.case_number


class ChildCWCHistory(BaseContent):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, blank=False, null=False)
    last_date_of_cwc_order_or_review = models.DateField(blank=False, null=False)


    class Meta:
        verbose_name_plural = "Child CWC History"

    def __str__(self):
        return self.child.case_number         