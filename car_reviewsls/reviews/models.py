from django.db import models

class Review(models.Model):
    modelo = models.CharField(max_length=50)
    calificacion = models.IntegerField()
    aceptacion = models.IntegerField()
    marca = models.CharField(max_length=50)
    referencia = models.CharField(max_length=100)
    especificaciones_tecnicas = models.TextField()
    autor = models.CharField(max_length=50)
    pais = models.CharField(max_length=50)
    fecha = models.DateField()
    opinion_sin_definir = models.TextField(blank=True, null=True)
    opinion_positiva = models.TextField(blank=True, null=True)
    opinion_negativa = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.marca} {self.referencia} - {self.modelo}"
