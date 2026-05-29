# Entia Integration (dsoklic)

Integration for the Entia smart home platform at `https://api.entia.si/`.

## API overview

Authentication: `POST /login` → JWT bearer token. The client re-authenticates once on 401 before raising `AuthError`.

### Endpoints

| Endpoint | Returns |
|---|---|
| `GET /flat` | Flat structure with device labels (see below) |
| `GET /flat/device` | Device list with current attribute values (see below) |
| `PUT /flat/device/{id}/attribute/{attrId}` | Set attribute value, body `{"value": ...}` |

### `GET /flat` response shape
```json
{
  "flat": {
    "floors": [{
      "rooms": [{
        "id": 2978,
        "label": "Dnevna",
        "devices": [{"id": 42467, "label": "1.1 dnevna", "type": 4}]
      }]
    }]
  }
}
```
Device labels use HTML entities (e.g. `&#381;` = Ž). The coordinator decodes them with `html.unescape()`.
`type: 4` = light device. There is no flat-level `id` or `name` in the response.

### `GET /flat/device` response shape
```json
{
  "connected": 1,
  "timezone": "Europe/Ljubljana",
  "devices": [{"id": 42467, "device_type_id": 400, "room_id": 2978,
               "attributes": [{"id": 401, "timestamp": 1780034143, "value": 0}],
               "settings": [...]}]
}
```
Attributes are inline — no per-device requests needed. `attribute_id 401` = light on/off state (1 = on, 0 = off).

## Coordinator update cycle

Each 30-second poll makes two requests:
1. `GET /flat` → build `{device_id: label}` map via `_build_label_map()`
2. `GET /flat/device` → device states with inline attributes

Lights are identified by the presence of `attribute_id 401` in their attributes dict.

## Config flow

Unique ID is the username (no flat-level ID is exposed by the API). Title is `Entia ({username})`.
Connectivity is verified by calling `authenticate()` + `get_flat()` before creating the entry.
