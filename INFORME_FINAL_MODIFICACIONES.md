# INFORME FINAL DE MODIFICACIONES TFG
**Fecha:** 15 de Enero 2026
**Versión:** 3.0 (Enterprise Academic)

Este documento resume las intervenciones técnicas realizadas en el proyecto para elevar el nivel académico y profesional del Trabajo de Fin de Grado.

## 1. Validación Académica Rigurosa (Modelado)
Se ha sustituido la validación aleatoria (`train_test_split`) por una validación temporal estricta para evitar el *Data Leakage*.

*   **Implementación**: `TimeSeriesSplit` (Scikit-Learn).
*   **Configuración**: 5 Folds (Ventana Expansiva).
*   **Justificación**: En predicción deportiva, no se puede entrenar con partidos del futuro para predecir el pasado. Esta metodología respeta la cronología de los eventos.
*   **Archivos Afectados**: `train_model.py` (reescrito completamente), `validation_metrics.json` (nuevo artifact de salida).

## 2. Dashboard "LaLiga Enterprise" (Visualización)
Se ha rediseñado la interfaz de usuario `app_dashboard.py` desde cero, abandonando la estética de "prototipo" por una profesional.

*   **Diseño**:
    *   Tema Oscuro Corporativo (`#0a0e27`).
    *   Eliminación de emojis informales.
    *   Uso de CSS personalizado para fuentes y tarjetas tipo "Glassmorphism".
*   **Estructura Modular**:
    *   **Tab 1: Live Market**: Comparativa de Cuotas (Winamax) vs Modelo (EV+).
    *   **Tab 2: Tactical Scouting**: Gráfico de Radar comparativo (Ataque, Defensa, Posesión, Intensidad) usando datos reales del dataset.
    *   **Tab 3: Historical Audit**: Transparencia total mostrando las métricas de varianza del modelo en los 5 folds temporales.
*   **Corrección de Errores**:
    *   Se solucionó el *crash* por nombres de columnas (`Home_Team` -> `HomeTeam`).
    *   Se implementó un mapeo de logos robusto para eliminar problemas con tildes (Atlético, Alavés, etc.).

## 3. Ingeniería de Datos & Notebooks
Se han actualizado los entregables académicos para que coincidan con el código de producción.

*   **Notebook 01 (Ingeniería)**: Refleja la lógica v3.0 (Field Tilt, xG Proxy, limpieza de duplicados).
*   **Notebook 02 (Entrenamiento)**: Incluye el código de `TimeSeriesSplit` para demostrar la rigorosidad en la memoria escrita.
*   **Datos**: Se ha verificado que el modelo trabaja con el dataset procesado `df_final_app.csv`.

## 4. Estado Actual del Repositorio
El proyecto se encuentra limpio y listo para presentación.

*   `app_dashboard.py`: Aplicación principal (Streamlit).
*   `train_model.py`: Script de entrenamiento y validación.
*   `df_final_app.csv`: Dataset final procesado (190 partidos).
*   `modelo_city_group.joblib`: Modelo entrenado final.

---
**Nota al Profesor**: La validación mediante series temporales suele arrojar métricas más humildes que la validación aleatoria, pero son métricas **reales y honestas**, lo cual es un punto fuerte en la defensa académica.
