# SLOs y Runbook de Incidentes [P4]

Este documento define SLOs y el procedimiento de respuesta ante incidentes para P3 (API qna-model-service).

## SLOs (Service Level Objectives)

- Disponibilidad mensual: 99.5%
- Latencia p95 de /predict: <= 300 ms (CPU) o <= 120 ms (GPU)
- Error rate de /predict: < 1%
- Freshness del modelo: artefacto <= 30 días

## SLIs (métricas)

- Availability: `up` en Prometheus (exportado por Kubernetes/proxy) combinado con health-check `/health`.
- Latency: histogram `prediction_duration_seconds` (ya expuesto por app).
- Error rate: counter `prediction_errors_total / predictions_total`.
- Freshness: timestamp del artefacto en `models/metrics.json` o etiqueta en el modelo.

## Dashboards (Prometheus/Grafana)

1. Importar `monitoring/grafana-dashboard.json` en Grafana.
2. Paneles recomendados:
   - Latencia: p50/p95 de `prediction_duration_seconds` (Range: 6h/24h/7d).
   - Throughput: `rate(predictions_total[5m])` por `model_version`.
   - Error rate: `rate(prediction_errors_total[5m]) / rate(predictions_total[5m])`.
   - Health: `up{job="qna"}` + estado `/health`.

Adjuntar capturas en `results/grafana/` (crear carpeta) y enlazar aquí:
- `results/grafana/latency_p95.png`
- `results/grafana/error_rate.png`

## Alertas (Reglas Prometheus)

- Latencia p95 > SLO por 15 min:
  ```promql
  histogram_quantile(0.95, sum(rate(prediction_duration_seconds_bucket[5m])) by (le)) > 0.3
  ```
- Error rate > 2% por 15 min:
  ```promql
  (sum(rate(prediction_errors_total[5m])) / sum(rate(predictions_total[5m]))) > 0.02
  ```
- Caída de instancia:
  ```promql
  up{job="qna"} == 0
  ```

## Runbook

1. Confirmar impacto
   - Revisar alertas en Prometheus/Alertmanager.
   - Verificar `GET /health`.
2. Diagnóstico rápido
   - Logs de app: `kubectl logs -l app=qna -f`.
   - Métricas: p95 latencia, error rate, throughput.
3. Acciones inmediatas
   - Reiniciar pod fallando.
   - Si error de modelo: revertir a versión anterior (rollback script o despliegue canary v1).
4. Mitigación y root cause
   - Capturar métricas antes/después.
   - Abrir incidente con timeline.
5. Postmortem
   - Documentar causa, impacto, acciones preventivas.
