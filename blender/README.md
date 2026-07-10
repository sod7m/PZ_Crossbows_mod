# Crossbow art workspaces

Each crossbow has an isolated workspace:

- `backup/game_current/` — snapshot of the model and textures currently used by the mod.
- `backup/original_before_detailed/` — Crude Crossbow's pre-detail source snapshot.
- `work/models/` and `work/textures/` — editable Blender files, generated FBX files, and texture drafts.
- `export/` — release-ready assets before copying them into the mod.
- `tools/` — Blender automation for that crossbow.

Crossbow folders: `crude_crossbow`, `improved_crossbow`, `compound_crossbow`, and `hand_crossbow`.
`shared/backup/PZCrossbows_models.txt` records the model definitions and attachments for this baseline.
