import re

with open('core/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure we import Resena if it's not already imported
if 'from .models import' in content and 'Resena' not in content:
    content = re.sub(
        r'(from \.models import.*?)(?=\n)',
        r'\1, Resena',
        content,
        count=1
    )

resena_view = '''
class CrearResenaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        puntuacion = request.data.get('puntuacion')
        comentario = request.data.get('comentario', '')

        if not puntuacion:
            return Response({'detail': 'La puntuacion es obligatoria.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            puntuacion = int(puntuacion)
            if puntuacion < 1 or puntuacion > 5:
                raise ValueError
        except ValueError:
            return Response({'detail': 'La puntuacion debe ser un numero entre 1 y 5.'}, status=status.HTTP_400_BAD_REQUEST)
        
        Resena.objects.create(
            usuario=request.user,
            puntuacion=puntuacion,
            comentario=comentario
        )
        return Response({'detail': 'Resena guardada exitosamente.'}, status=status.HTTP_201_CREATED)
'''

if 'class CrearResenaView' not in content:
    with open('core/views.py', 'w', encoding='utf-8') as f:
        f.write(content + resena_view)
    print("Resena view added")
else:
    print("Resena view already exists")
