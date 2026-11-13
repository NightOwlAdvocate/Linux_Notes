# Kubernetes за два дня: план для ChronoRec и MinFri

Цель не в том, чтобы «выучить весь Kubernetes». За два дня нужно научиться объяснять, что происходит в уже существующей лаборатории ChronoRec, и самостоятельно диагностировать несколько типичных отказов.

## Что у тебя уже есть

В публичном `chronorec-k8s-infrastructure` уже реализованы синтетический FastAPI-сервис, Dockerfile, локальный двухузловой кластер `kind`, Helm chart, probes, resource limits, PDB, NetworkPolicy, CI smoke test, Prometheus/Grafana и четыре сценария отказа. Это реальная учебная работа, но не production.

В MinFri уже есть программный прототип: backend, Face UI, WebSocket, state machine, push-to-talk и тесты. STT/LLM/TTS пока fake providers; Raspberry Pi и MicroK8s не являются частью готового MVP.

## Ментальная модель за 10 минут

```text
Docker image → Deployment → Pod(ы)
                          ↓
                       Service
                          ↓
                         client

Helm chart = шаблоны и настройки этих объектов
kind = локальный учебный Kubernetes-кластер в Docker
kubectl = клиент для просмотра и изменения состояния кластера
```

- **Pod** — запускаемый экземпляр одного или нескольких контейнеров; он заменяемый, а не «вечный сервер».
- **Deployment** — желаемое количество одинаковых Pod и стратегия обновления.
- **Service** — стабильная точка доступа к меняющимся Pod.
- **readiness probe** — можно ли уже направлять трафик; **liveness probe** — нужно ли перезапустить зависший контейнер.
- **requests/limits** — сколько ресурсов планируется и какой максимум разрешён.

Официальные материалы: [Kubernetes Basics](https://kubernetes.io/docs/tutorials/kubernetes-basics/), [learning environment](https://kubernetes.io/docs/setup/learning-environment/) и [probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/).

## День 1 — понять путь запроса

### Блок 1, 60 минут: приложение до Kubernetes

1. В `chronorec-k8s-infrastructure` прочитай `README.md` и `docs/ARCHITECTURE.md`.
2. Запусти API обычным способом, без Kubernetes.
3. Проверь `/healthz`, `/readyz`, `/metrics` и один бизнес-endpoint.
4. Своими словами ответь: что проверяет каждый endpoint и почему `/readyz` не равен `/healthz`.

Результат: ты понимаешь приложение до того, как добавляешь оркестратор.

### Блок 2, 90 минут: image, Pod, Deployment, Service

1. Запусти `./scripts/check-environment.sh`, затем `./scripts/bootstrap-lab.sh`.
2. Нарисуй цепочку: source → image → Deployment → Pod → Service → port-forward.
3. Выполни и объясни каждую команду:

   ```bash
   kubectl get nodes
   kubectl -n chronorec-lab get deploy,pods,svc -o wide
   kubectl -n chronorec-lab describe deployment chronorec-demo
   kubectl -n chronorec-lab logs deployment/chronorec-demo --tail=30
   ```

4. Найди в Helm chart image, replica count, probes, ports и limits.

Результат: ты можешь показать, где в YAML появляется каждый объект и как запрос доходит до FastAPI.

### Блок 3, 60 минут: безопасный отказ

1. Удали один Pod по инструкции из `docs/runbooks/FAILURE_SCENARIOS.md`.
2. Наблюдай, как Deployment создаёт замену.
3. Запиши пять строк: ожидание, команда, наблюдение, механизм восстановления, доказательство.

### Самопроверка дня 1, 30 минут

Без подсказок объясни:

- почему удаление Pod не удаляет Deployment;
- зачем Service, если Pod уже имеет IP;
- чем readiness отличается от liveness;
- почему два replica ещё не означают полноценную high availability;
- почему `kind` подходит для lab, но сам по себе не доказывает production-опыт.

## День 2 — обновление, диагностика и observability

### Блок 1, 90 минут: rollout и rollback

1. Посмотри текущий rollout и историю Helm.
2. Запусти сценарий failed readiness rollout из runbook.
3. Используй только наблюдение до исправления:

   ```bash
   kubectl -n chronorec-lab get pods
   kubectl -n chronorec-lab describe pod <pod-name>
   kubectl -n chronorec-lab logs <pod-name> --previous
   helm -n chronorec-lab history chronorec-demo
   ```

4. Объясни, кто заметил ошибку, почему Pod не получил трафик и как произошёл rollback.

### Блок 2, 90 минут: CrashLoopBackOff и OOMKilled

1. Выполни оба сценария из runbook по одному.
2. Для каждого начни с `get` → `describe` → `logs`, а не с угадывания исправления.
3. Зафиксируй различие:

   - CrashLoopBackOff описывает повторяющиеся неуспешные запуски;
   - OOMKilled указывает, что процесс был завершён из-за памяти;
   - restart лечит состояние процесса, но не первопричину плохой конфигурации.

### Блок 3, 60 минут: метрики без магии

1. Установи monitoring скриптом репозитория.
2. Найди метрики API в Prometheus и соответствующий dashboard в Grafana.
3. Сопоставь один симптом из `kubectl` с одной метрикой.
4. Запиши, чего dashboard не доказывает: корректность данных, качество backup и реальную пользовательскую доступность.

### Блок 4, 45 минут: применить к MinFri на бумаге

Не деплой MinFri. Сделай design exercise:

- какой компонент можно было бы сделать stateless Deployment;
- какие данные нельзя терять при замене Pod;
- почему микрофон, speaker, GPIO и локальный Face UI усложняют кластеризацию;
- какая реальная проблема должна появиться, чтобы Kubernetes стал оправдан.

Вывод для текущего этапа: сначала закончить надёжный software MVP, затем контейнер, и только потом — отдельный MicroK8s experiment на Ubuntu.

## Критерий готовности через два дня

Ты готова обсуждать lab на собеседовании, если можешь без заученных определений:

1. нарисовать путь запроса;
2. объяснить Deployment, Pod, Service и probes на примере ChronoRec;
3. диагностировать Pod через `get`, `describe`, `logs`;
4. показать rollout/rollback и один failure scenario;
5. честно назвать границу: local verified lab, не production;
6. объяснить, почему MicroK8s для MinFri — будущий experiment после MVP.

После практики удали только учебный кластер:

```bash
kind delete cluster --name chronorec-lab
```
