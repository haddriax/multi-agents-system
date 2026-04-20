# Robot Mission MAS 2026

Dépôt de projet Multi-Agent Systems.  
Ce projet a été développé dans le cadre du cours MAS 2026, développé par le **Groupe 9** : Maëlys Hanoire, Raphaël Vignal & Gaël Garnier.

---

## Problématique

Nous simulons un environnement hostile (radioactif) dans lequel des robots doivent accomplir la mission suivante : explorer l'environnement, collecter des déchets radioactifs, les fusionner, et déposer le résultat final dans une zone de dépôt précise.

L'environnement est une grille 2D divisée en trois zones verticales de radioactivité croissante (z1, z2, z3). La zone de dépôt est située sur la colonne la plus à droite de la grille.

Il existe trois types de robots, chacun traitant un niveau de déchet spécifique :

| Type de robot | Déchet traité | Accès aux zones | Comportement |
|---|---|---|---|
| Vert | Déchet vert | z1 seulement | Ramasse 2 déchets verts, les fusionne en 1 jaune, dépose à la frontière z1/z2 |
| Jaune | Déchet jaune | z1 + z2 | Ramasse 2 déchets jaunes, les fusionne en 1 rouge, dépose à la frontière z2/z3 |
| Rouge | Déchet rouge | z1 + z2 + z3 | Ramasse 1 déchet rouge, le transporte jusqu'à la zone de dépôt |

La simulation se termine lorsque tous les déchets ont été collectés, fusionnés et déposés.

---

## Implémentation

### Agents

Toutes les entités de la simulation héritent de la classe `Agent` de Mesa. On sépare les agents actifs (robots, qui délibèrent) et les agents passifs (objets placés sur la grille mais qui n'agissent pas).

#### Robots

Les trois types de robots (Vert, Jaune, Rouge) partagent une grande partie de la logique. Plutôt que de dupliquer le code, nous avons séparé l'implémentation en deux couches :

- **`MesaAgentAdapter`** (`mesa_adapter.py`) : la seule classe qui interagit avec Mesa. Elle possède le robot, gère le `step()`, et expose les propriétés attendues par Mesa (`pos`, `unique_id`). Les sous-classes (`GreenAgent`, `YellowAgent`, `RedAgent`) définissent deux attributs de classe : `robot_type` et `MAX_ZONE`.
- **`RobotAgent`** (`robot_agent.py`) : Pas de dépendance à Mesa. Contient la `Memory` de l'agent et exécute la chaîne de handlers dans `deliberate()`.

Cette séparation casse le couplage Agent/Model de Mesa, ce qui a été un long problème dans notre implémentation.

#### Cycle des robots

À chaque step, `MesaAgentAdapter.step()` exécute le cycle suivant :

1. **Percevoir** : `SystemModel.perceive(agent)` construit une `Perception` à partir du capteur optique de l'agent (rayon 5).
2. **Mettre à jour la mémoire** — `robot.update_memory(perception)` écrit les lectures de cellules dans `Memory.belief_map`, puis vide la boîte mail.
3. **Délibérer** : `robot.deliberate()` parcourt la chaîne de handlers et retourne la première `Action` non nulle.
4. **Agir** : `SystemModel.do(agent, action)` exécute l'action et retourne un `ActionResult`.
5. **Retour d'information** : `robot.on_action_result(action, result)` dépile `planned_path[0]` après un déplacement réussi.

#### Chaîne de handlers

`deliberate()` itère une liste ordonnée par priorité de fonctions handlers.  
Chaque handler est une fonction pure `(Memory, tier, grid_dims) -> Action | None`. Le premier résultat non nul l'emporte.  
Cela permet de définir quel action va être exécutée par le robot.  

| Priorité | Handler | Se déclenche quand…                                                                  |
|---|---|--------------------------------------------------------------------------------------|
| 1 | `_handle_yield` | La cellule courante du robot est réservée par un autre, il se déplace pour la libérer |
| 2 | `_handle_merge` | Porte un déchet de son propre tier et se trouve sur un déchet identique au sol       |
| 3 | `_handle_deposit` | Porte un déchet fusionné (tier supérieur), navigue vers le point de dépôt            |
| 4 | `_handle_seek` | Un déchet de son tier est connu dans la belief map, le réserve et navigue vers lui   |
| 5 | `_handle_explore` | Se déplace vers la cellule inexplorée la plus proche                        |

Les robots Vert et Jaune utilisent `BASE_HANDLERS` (les cinq). Les robots Rouges utilisent `RED_HANDLERS` qui n'a pas l'étape de fusion.

#### Agents passifs

- **`Waste`** : placé sur la grille à l'initialisation. Ramassé et supprimé par les robots.
- **`Radioactivity`** : un par cellule, contient le niveau de radioactivité (0–1) qui détermine la zone (z1 ≤ 0.33 < z2 ≤ 0.66 < z3).
- **`WasteDisposalZone`** : agent unique placé aléatoirement dans la colonne la plus à droite. Comptabilise aussi les `waste_received`.

### Navigation

Les robots naviguent avec **A\*** sur leur `belief_map`. Les cellules connues comme occupées par un autre robot sont bloquées.

Si le chemin devient bloqué par un robot qui s'y est déplacé après la planification, l'agent replanie son chemin avant de décider d'attendre.  
Cela évite les deadlocks statiques où deux agents s'attendent, ce qui a été un gros problème lors du développement.

### Coordination et Communication entre robots

Les robots se coordonnent via trois mécanismes qui s'appuient sur la messagirie :

1. **Système de réservation** : avant de naviguer vers un déchet, un robot fait une `ReserveAction`. `SystemModel` maintient un registre `pos → (is_priority, agent_id)`.

2. **Diffusion d'annulation** : lorsqu'un robot ramasse ou fusionne un déchet, `SystemModel` envoie un `WasteCancelledMessage` à tous les robots du même tier. Les destinataires effacent la position de leur belief map.

3. **Diffusion de découverte** : lors de `update_memory`, un robot qui perçoit un nouveau déchet de son tier (qui n'est pas déjà sa cible) le place dans `memory.outbox`. Après que tous les agents ont agi, `SystemModel._process_outboxes()` distribue des `WasteDiscoveredMessage` aux pairs du même tier. Cela permet aux robots de partager l'information de la localisaton des `Waste`.

Lors d'un transfert, le robot qui dépose notifie aussi immédiatement les robots du tier suivant via `WasteDiscoveredMessage`.

## Choix majeurs de conception

- **Actions en données pures** : Inspiré d'un Command Pattern, mais dur à réaliser avec Mesa. les agents produisent des objets `Action` (sans logique), que `SystemModel.do()` exécute.  
- **Belief map** : les agents ne connaissent que ce qu'ils ont vu ou reçu par message.
- **Adaptateur pour Mesa** : isoler Mesa dans `MesaAgentAdapter` signifie que `RobotAgent` et tous les handlers n'ont aucun import Mesa. Cela évite des imports cycliques.
- **Liste de handlers** : objectif de pouvoir changer les comportements facilement. Pour ajouter un nouveau comportement, il faut juste ajouter une fonction insérée à la bonne position dans la liste.

---

## Résultats

Avec la configuration par défaut (grille 80×40, 5 robots par type, 20 déchets verts / 8 jaunes / 6 rouges), la simulation se termine en environ **250 à 350 steps** :

```
[Victory] All waste cleared at step 307
  Initial: G=20 Y=8 R=6
  Disposed: 15 [OK]
```

Le nombre attendu est `R + (Y + G//2)//2 = 6 + (8 + 10)//2 = 15`. La vérification de cohérence confirme qu'aucun déchet n'a été perdu.  
On constate encore des dealocks lorsque le spawn du `WasteDisposalZone` est dans un coin, ce qui peut créer un blocage de robots.
---

## Lancement du projet

```bash
uv sync
uv run python -m Raphael_Maelys_Gael_robot_mission_MAS2026.run
```

Cela ouvre le visualiseur Solara dans le navigateur.

---

## Structure du projet

```
Raphael_Maelys_Gael_robot_mission_MAS2026/
├── run.py                  # point d'entrée à exécuter
├── system/
│   ├── system_model.py     # modèle Mesa (perception, dispatch d'actions, coordination)
│   ├── config.py           # chargement de config.yaml
│   ├── entities/
│   │   ├── agents/         # GreenAgent, YellowAgent, RedAgent, MesaAgentAdapter,
│   │   │                   # RobotAgent, listes de handlers
│   │   └── objects/        # Waste, Radioactivity, WasteDisposalZone
│   ├── models/             # structures de données pures, pas de logique
│   ├── map/                # NavigableGrid
│   └── tools/              # Spawner, Pathfinder A*
└── viewer/                 # composants du visualiseur Solara
```
