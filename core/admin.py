# Developed by FireSeed - Fueling Innovation
from django.contrib import admin
from .models import (
    ConfiguracionGlobal, Usuario, Plan, Suscripcion,
    Clase, Turno, Recurrencia, Reserva
)

@admin.register(ConfiguracionGlobal)
class ConfiguracionGlobalAdmin(admin.ModelAdmin):
    list_display = ('id', 'cupo_maximo_defecto', 'cupo_minimo_defecto', 'horas_limite_cancelacion', 'horas_evaluacion_automatica', 'dias_vencimiento_plan', 'dias_alerta_vencimiento', 'updated_at')
    readonly_fields = ('id', 'updated_at')

    def has_add_permission(self, request):
        # Only allow one configuration instance
        if ConfiguracionGlobal.objects.exists():
            return False
        return super().has_add_permission(request)

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('email', 'nombre', 'apellido', 'rol', 'is_active', 'is_staff')
    list_filter = ('rol', 'is_active', 'is_staff')
    search_fields = ('email', 'nombre', 'apellido')
    readonly_fields = ('id', 'created_at', 'google_id')

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cantidad_clases', 'precio', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('nombre',)

@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'plan', 'clases_restantes', 'fecha_inicio', 'fecha_vencimiento', 'estado')
    list_filter = ('estado',)
    search_fields = ('usuario__email', 'usuario__nombre', 'usuario__apellido')
    autocomplete_fields = ('usuario', 'plan')

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

@admin.register(Recurrencia)
class RecurrenciaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'clase', 'dia_semana', 'hora_inicio', 'is_active')
    list_filter = ('dia_semana', 'is_active', 'clase')
    autocomplete_fields = ('usuario', 'clase')

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('turno', 'usuario', 'suscripcion', 'estado', 'es_recurrente', 'created_at')
    list_filter = ('estado', 'es_recurrente')
    search_fields = ('usuario__email', 'usuario__nombre')
    autocomplete_fields = ('turno', 'usuario', 'suscripcion')
