# Perfiles de manijas de válvula (planos Fadesa)

Genera `flama/perfiles_valvula.py` a partir de los planos vectoriales Fadesa (no incluidos en el repo).

1. `regiones.py <pdf> x0 y0 x1 y1 600 <salida.png>`: rasteriza la zona de la válvula a 600 dpi y numera las regiones
   cerradas del dibujo (componentes del fondo entre trazos).
2. Mirando la imagen numerada se eligen las regiones de cada pieza (palanca, manija, cuerpo) y en `perfiles.py` se
   pasan a contorno en mm: escala del rótulo (1 kg 1:2,5; 5 kg 1:4), x = 0 en el eje de la válvula, z = 0 en la cara
   superior del cuello (línea entre collarín y rosca).

Zonas usadas (puntos PDF): 1 kg `290 55 445 140`; 5 kg `395 70 525 120`.
