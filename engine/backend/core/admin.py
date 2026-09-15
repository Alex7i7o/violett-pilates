from django.contrib import admin
from .models import (
     Usuario, Clase, Turno,  Reserva
)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('email', 'nombre', 'apellido', 'rol', 'is_active', 'is_staff')
    list_filter = ('rol', 'is_active', 'is_staff')
    search_fields = ('email', 'nombre', 'apellido')
    readonly_fields = ('id', 'created_at', 'google_id')

@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'duracion_minutos', 'cupo_maximo', 'cupo_minimo', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('nombre',)

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ('clase', 'fecha', 'hora_inicio', 'hora_fin', 'cupo_actual', 'estado')
    list_filter = ('estado', 'fecha', 'clase')
    search_fields = ('clase__nombre',)
    autocomplete_fields = ('clase',)


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('turno', 'usuario', 'estado', 'es_recurrente', 'created_at')
    list_filter = ('estado', 'es_recurrente')
    search_fields = ('usuario__email', 'usuario__nombre')
    autocomplete_fields = ('turno', 'usuario')
