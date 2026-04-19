# Ajouter une nouvelle action

## 1. Déclarer l'action (`src/system/models/action.py`)

```python
@dataclass(frozen=True)
class MyAction(Action):
    some_field: int  # payload si nécessaire
```

## 2. Implémenter l'exécution (`src/system/system_model.py`)

```python
# dans do()
case MyAction(): return self._do_my_action(agent, action)

# nouveau handler
def _do_my_action(self, agent: MesaAgentAdapter, action: MyAction) -> ActionResult:
    ...
    return ActionSuccess()
```

## 3. Produire l'action (`src/system/entities/agents/handlers.py`)

Retourner `MyAction()` depuis le handler approprié dans la chaîne `HANDLERS`.

Les actions sont des données pures, toute la logique d'exécution va dans `SystemModel` sinon le coupling Agent/Model de Mesa est encore problématique.
