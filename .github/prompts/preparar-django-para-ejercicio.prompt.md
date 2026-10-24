---
name: preparar-django-para-ejercicio
description: "Prepara o adapta este proyecto Django para un nuevo ejercicio académico o prueba, reutilizando la estructura existente con cambios controlados."
agent: agent
---

# Adaptar este proyecto Django a otro ejercicio

Actúa como ingeniero Django senior. Prepara este repositorio para el siguiente ejercicio usando la estructura y convenciones que realmente existan en el workspace. No asumas que la descripción del usuario coincide con el código.

## Datos del nuevo ejercicio

- Nombre del proyecto: [COMPLETAR]
- Objetivo y contexto: [COMPLETAR]
- Requisitos funcionales: [PEGAR LA CONSIGNA COMPLETA]
- Requisitos técnicos o restricciones del profesor: [COMPLETAR O INDICAR "NINGUNO"]
- Elementos del proyecto actual que deben conservarse: [COMPLETAR O INDICAR "DECIDIR SEGÚN REUTILIZACIÓN"]
- Diseño o referencias visuales: [COMPLETAR O INDICAR "SIN REFERENCIA"]

## Procedimiento

1. Inspecciona `manage.py`, settings, URLs, apps, modelos, migraciones, vistas, formularios, templates, archivos estáticos, dependencias y pruebas. Revisa también instrucciones del repositorio. Usa las rutas y nombres encontrados; no inventes apps ni presumas que existe `base.html`.
2. Resume en pocas líneas qué se puede reutilizar, qué falta y qué partes podrían quedar obsoletas. Si un requisito crítico no está especificado, pregunta antes de tomar una decisión que cambie datos, dominio o comportamiento. Para decisiones reversibles, adopta la opción más sencilla y explícitala.
3. Propón una correspondencia breve entre requisitos y archivos o módulos. Después implementa el ejercicio completo en el repositorio, respetando el estilo existente y manteniendo las responsabilidades separadas.
4. Implementa modelos y sus migraciones; vistas, formularios y validaciones; URLs con nombres; templates que extiendan una plantilla base cuando exista o créala siguiendo el diseño acordado; estáticos; registro administrativo; y API REST solo si la consigna lo requiere.
5. Añade o actualiza pruebas para los flujos principales y los casos de error relevantes. No reemplaces datos del usuario ni borres bases de datos, migraciones, archivos o configuraciones existentes para simplificar el trabajo.
6. Registra las dependencias necesarias en el manifiesto que use el proyecto. No instales paquetes innecesarios ni guardes credenciales. Mantén secretos fuera del código y señala configuraciones locales que deban cambiarse antes de producción.
7. Ejecuta las validaciones adecuadas disponibles: `manage.py check`, detección de cambios de migración, migraciones y pruebas del proyecto. Si alguna no se puede ejecutar, explica el bloqueo y el comando pendiente.
8. Revisa el diff para confirmar que los cambios estén limitados al ejercicio, que los enlaces y nombres de URL coincidan y que no haya plantillas huérfanas o rutas rotas.

## Criterios de finalización

- Todos los requisitos entregados tienen implementación identificable y verificable.
- El proyecto inicia y las rutas principales responden correctamente.
- Los modelos pueden migrarse y el panel administrativo permite gestionarlos cuando aplique.
- Los formularios muestran errores útiles y protegen los envíos con CSRF.
- Las pruebas cubren los comportamientos nuevos importantes.
- Se informa qué archivos se modificaron, qué comandos se ejecutaron y cualquier requisito o decisión pendiente.

## Límites

- Trabaja en el repositorio actual; no crees un proyecto paralelo.
- No hagas refactors ajenos al ejercicio ni cambies nombres públicos sin necesidad.
- No elimines ni sobrescribas cambios preexistentes del usuario.
- No afirmes que una validación pasó si no se ejecutó.
- Si la consigna pide entregar el código completo, incluye en la respuesta el contenido completo de cada archivo nuevo o modificado, organizado por ruta.
