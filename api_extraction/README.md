# Proxmox API Extraction

Extraction complète de l'API Proxmox VE depuis `apidoc.js` et conversion en spécification OpenAPI 3.0.

## Utilisation

```bash
# Extraire et générer l'OpenAPI complet
python extract_and_combine.py
```

Cette commande va :
1. Parser `../apidoc.js` (3.5 MB)
2. Extraire tous les endpoints récursivement
3. Générer les fichiers JSON par section
4. Créer `proxmox_api_complete.json` - Spécification OpenAPI 3.0 avec catégories
5. Analyser les helpers et générer `API_COVERAGE_ANALYSIS.md`

## Fichiers

**Script:**
- `extract_and_combine.py` - Script d'extraction et génération OpenAPI

**Résultats générés automatiquement:**
- `proxmox_api_complete.json` (2.2 MB) - Format OpenAPI 3.0 avec 26 catégories, 628 endpoints
- `API_COVERAGE_ANALYSIS.md` (généré automatiquement) - Analyse de couverture API vs helpers

**Documentation:**
- `README.md` - Ce fichier

**Notes:**
- Les fichiers `*_endpoints.json` temporaires par section sont créés puis supprimés automatiquement
- `API_COVERAGE_ANALYSIS.md` est régénéré à chaque exécution avec les stats à jour

## Statistiques API

```
Total: 628 endpoints sur 410 chemins

Par section:
  /nodes     345 (55%)  - VMs, containers, storage, réseau
  /cluster   226 (36%)  - Config cluster, HA, backups
  /access     44 (7%)   - Auth, users, permissions
  /pools       7 (1%)   - Resource pools
  /storage     5 (1%)   - Config stockage

Par méthode HTTP:
  GET        314 (50%)
  POST       161 (26%)
  PUT         79 (13%)
  DELETE      74 (12%)

Catégories: 26 tags thématiques
  - Infrastructure: nodes, cluster, access, pools, storage
  - VMs: virtual-machines, qemu-agent, vm-control, snapshots
  - Réseau: networking, firewall, software-defined-networking
  - Stockage: ceph-storage, disk-management, backup
  - Sécurité: certificates, users, groups, roles, permissions
```

## Structure OpenAPI

Le fichier `proxmox_api_complete.json` suit le format OpenAPI 3.0 :

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Proxmox VE API",
    "version": "8.x"
  },
  "tags": [
    {"name": "virtual-machines", "description": "QEMU VM operations"},
    {"name": "containers", "description": "LXC container operations"},
    ...26 catégories
  ],
  "paths": {
    "/nodes/{node}/qemu/{vmid}/status/start": {
      "post": {
        "tags": ["nodes", "virtual-machines", "vm-control"],
        "summary": "Start virtual machine",
        "parameters": [...],
        "responses": {...},
        "security": [{"PVEAuth": []}]
      }
    },
    ...410 chemins
  },
  "components": {
    "securitySchemes": {
      "PVEAuth": {...}
    }
  },
  "x-statistics": {...}
}
```

## Utilisation avec outils OpenAPI

**Swagger UI:**
```bash
docker run -p 8080:8080 \
  -v $(pwd):/usr/share/nginx/html/api \
  swaggerapi/swagger-ui
# Ouvrir: http://localhost:8080/?url=api/proxmox_api_complete.json
```

**OpenAPI Generator:**
```bash
openapi-generator generate \
  -i proxmox_api_complete.json \
  -g python \
  -o generated/
```

**Analyse avec Python:**
```python
import json

# Charger l'OpenAPI
with open('proxmox_api_complete.json') as f:
    api = json.load(f)

# Trouver tous les endpoints VM
vm_paths = [p for p in api['paths'] if '/qemu/' in p]
print(f"VM endpoints: {len(vm_paths)}")

# Vérifier un endpoint spécifique
if '/nodes/{node}/qemu/{vmid}/status/start' in api['paths']:
    op = api['paths']['/nodes/{node}/qemu/{vmid}/status/start']['post']
    print(f"Tags: {op['tags']}")
    print(f"Parameters: {[p['name'] for p in op['parameters']]}")
```

## Couverture des helpers

D'après `API_COVERAGE_ANALYSIS.md` (généré automatiquement) :

**Statistiques globales:**
- Total API Endpoints: 628
- Total Helper Methods: 280
- Total Helper Lines: 8,172
- Helper Files: 11

**Par section:**

| Section | API Endpoints | Primary Helpers | Estimated Coverage |
|---------|---------------|-----------------|-------------------|
| /access | 44 | access.py | ~60-70% |
| /cluster | 226 | cluster.py, sdn.py, notifications.py | ~30-40% |
| /nodes | 345 | nodes.py, ceph.py, disks.py, firewall.py | ~40-50% |
| /pools | 7 | pools.py | ~100% ✓ |
| /storage | 5 | storage.py | ~100% ✓ |

**Fonctionnalités manquantes principales:**
- Network interface management (~7 endpoints, 0%)
- Certificate management (~7 endpoints, 0%)
- Cluster firewall (~31 endpoints, 0%)
- Device mapping PCI/GPU (~16 endpoints, 0%)
- APT package management (~4 endpoints, 0%)
- Subscription management (~4 endpoints, 0%)

## Source de données

Le fichier `apidoc.js` est téléchargé depuis la documentation officielle Proxmox :
- **Page:** https://pve.proxmox.com/pve-docs/api-viewer/
- **Fichier direct:** https://pve.proxmox.com/pve-docs/api-viewer/apidoc.js

## Maintenance

Mettre à jour après une nouvelle version de Proxmox :

```bash
# 1. Télécharger le nouveau apidoc.js depuis la doc officielle
wget https://pve.proxmox.com/pve-docs/api-viewer/apidoc.js -O ../apidoc.js

# Ou avec curl
curl https://pve.proxmox.com/pve-docs/api-viewer/apidoc.js -o ../apidoc.js

# 2. Re-extraire
python extract_and_combine.py

# 3. Vérifier les changements
git diff proxmox_api_complete.json
```

## License

Données extraites de l'API Proxmox VE (AGPL-3.0).
