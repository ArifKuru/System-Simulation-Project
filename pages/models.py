from django.db import models

class Projects(models.Model):
    project_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='project_images/', blank=True, null=True,default='project_images/default.png')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.project_name


class Stocks(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.CASCADE, related_name='stocks')
    name = models.CharField(max_length=100)
    value = models.FloatField()

    def __str__(self):
        return f"{self.name} ({self.value})"