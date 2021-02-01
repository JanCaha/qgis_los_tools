---
title: Workflow {{ env.WORKFLOW }} failed for {{ env.DOCKER_TAG }}
labels: bug
---

Workflow {{ env.WORKFLOW }} failed for qgis/qgis:{{ env.DOCKER_TAG }} at: {{ date | date('YYYY-MM-DD HH:mm:ss') }}

[Link for the action result.]({{ env.URL_ACTION }})