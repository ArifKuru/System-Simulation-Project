from django.db import models

class Projects(models.Model):
    project_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='project_images/', blank=True, null=True,default='project_images/default.png')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.project_name


class Stocks(models.Model):
    # Each stock (state variable) belongs to a specific project.
    # If the project is deleted, all associated stocks will also be deleted.
    project = models.ForeignKey(Projects, on_delete=models.CASCADE, related_name='stocks')

    # Name of the stock, used to identify it within the simulation.
    name = models.CharField(max_length=100)

    # Current value of the stock. This value may change as the simulation runs.
    value = models.FloatField()

    # Initial value of the stock at the start of the simulation.
    # This is set automatically when the stock is first saved and is not editable by users.
    # It is used to reset or restart the simulation from its original state.
    initial_value = models.FloatField(editable=False)

    def save(self, *args, **kwargs):
        # If this is a new stock and the initial_value hasn't been set,
        # set it equal to the current value.
        if self._state.adding and self.initial_value is None:
            self.initial_value = self.value
        super().save(*args, **kwargs)

    def __str__(self):
        # Defines how this stock will appear in the admin panel or debug output.
        return f"{self.name} ({self.value})"


class Events(models.Model):
    # The stock that this event is associated with (the stock whose rate this event depends on).
    stock = models.ForeignKey(Stocks, on_delete=models.CASCADE, related_name='events')

    # Name of the event, used to describe it in the interface.
    name = models.CharField(max_length=100)

    # Probability or rate expression for the event to occur.
    # Can be a static number like "0.5" or a dynamic expression like "stock('X') * 0.3".
    possibility = models.CharField(
        max_length=100,
        help_text="Ex: 0.5 or stock('X') * 0.3"
    )

    def __str__(self):
        # String representation of the event, shown in admin panel or logs.
        return f"{self.name})"


class Effects(models.Model):
    # The event that triggers this effect.
    event = models.ForeignKey('Events', on_delete=models.CASCADE, related_name='effects')

    # The stock that will be affected when the event occurs.
    target_stock = models.ForeignKey(Stocks, on_delete=models.CASCADE)

    # Expression defining how the stock is affected, such as "*2", "+3", "- stock('Y')", etc.
    # This determines the change to be applied to the target stock.
    effect_expression = models.CharField(
        max_length=100,
        help_text='Ex: "*2", "+ stock(\\"Y\\")", "-3"'
    )

    def __str__(self):
        # String representation showing the effect in a readable format.
        return f"{self.event.name} → {self.target_stock.name} {self.effect_expression}"