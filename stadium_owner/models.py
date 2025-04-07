from django.contrib.gis.db import models
from django.conf import settings
from django.contrib.gis.geos import Point



class FacilityType(models.Model):
    
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Amenity(models.Model):
    
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class VenueImage(models.Model):
   
    stadium = models.ForeignKey("StadiumDetails", on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="venue_images/")  
    def __str__(self):
        return self.image.url

class StadiumDetails(models.Model):
    """ Store Stadium details """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="stadium_profile")
    stadium_name = models.CharField(max_length=255, db_index=True)  
    facility_types = models.ManyToManyField(FacilityType) 
    contact_number = models.CharField(max_length=15)

    
    location = models.PointField(geography=True, null=True, blank=True)  

    amenities = models.ManyToManyField(Amenity) 
    business_license = models.FileField(upload_to="licenses/")
    ownership_proof = models.FileField(upload_to="ownership_proofs/")  
    terms_accepted = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.stadium_name}"

    class Meta:
        indexes = [
            models.Index(fields=["stadium_name"]),
        ]