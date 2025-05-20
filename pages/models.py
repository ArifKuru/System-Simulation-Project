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
    initial_value = models.FloatField(editable=False)

    def save(self, *args, **kwargs):
        # Eğer ilk kez kaydediliyorsa initial_value'yu ayarla
        if self._state.adding and self.initial_value is None:
            self.initial_value = self.value
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.value})"






class Events(models.Model):
    stock = models.ForeignKey(Stocks, on_delete=models.CASCADE, related_name='events')
    name = models.CharField(max_length=100)
    possibility = models.CharField(max_length=100, help_text="Ex: 0.5 or stock('X') * 0.3")
    effect = models.CharField(max_length=20, help_text="Effect like '*2', '+5', '-3' etc.")

    def __str__(self):
        return f"{self.name} ({self.effect})"

    def apply_effect(self, value):
        """
        Apply the effect to a given value (if it's valid).
        """
        try:
            return eval(f"{value}{self.effect}")
        except Exception:
            return value  # fallback if effect is invalid

