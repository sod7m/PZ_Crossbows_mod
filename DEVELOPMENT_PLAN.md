# PZ Crossbows Development Plan

## Goal

Build a standalone Project Zomboid `42.19.0` crossbow mod in `E:\PZCrossbows\PZCrossbows`.

`PWPNXB` is used only as a temporary development base for mechanics, textures, models, and sounds. Before final Steam/GitHub release, the borrowed visual assets should be redrawn or replaced.

## Current Diagnosis

Paths used during investigation:

- Game: `D:\SteamLibrary\steamapps\common\ProjectZomboid`
- Reference mod: `E:\PZCrossbows\PWPNXB`
- New mod: `E:\PZCrossbows\PZCrossbows`
- Logs: `C:\Users\Dmytro\Zomboid`

The main bug found in the reference mod logs:

- `PWPNXBOnZombieDead(zPWPNXBClient.lua:175)`
- `PWPNXBOnZombieDead(zPWPNXBClient.lua:182)`
- `Cannot invoke "zombie.iso.IsoGridSquare.getObjects()" because "o.square" is null`
- The crash happens inside `sendAddItemToContainer(zombie:getInventory(), bolt)`.

The likely cause is that the reference mod adds a bolt to the zombie inventory during `OnZombieDead`, then immediately sends a container network packet while the killed zombie has no valid square. That can create ghost items that appear in the corpse inventory but cannot be picked up safely.

The second issue is recovery logic. The reference mod rolls every lodged bolt separately, so one corpse can contain both intact bolts and broken bolts. In this mod the rule should be cleaner: for each ammo type on a corpse, spawn either intact bolts or broken bolts, not both.

## Implemented Base

1. Workshop-style structure:
   - `PZCrossbows/workshop.txt`
   - `PZCrossbows/preview.png`
   - `PZCrossbows/Contents/mods/PZCrossbows/42/mod.info`
   - `PZCrossbows/Contents/mods/PZCrossbows/42/media/...`

2. Standalone module:
   - Module and item IDs use `PZCrossbows`.
   - Ammo registry uses only `PZCrossbows:wood_bolt` and `PZCrossbows:short_wood_bolt`.
   - No `PWPNXB` dependency remains in `mod.info`.

3. Bolt recovery fix:
   - Removed direct `sendAddItemToContainer` calls for zombie inventory during `OnZombieDead`.
   - Added items to corpse inventory only through container `AddItem("Module.Item")`.
   - Recovery chance is clamped to `0..100`.
   - Recovery rolls once per ammo type batch, so the corpse gets either intact bolts or broken bolts.
   - Build 42.19 can already place lodged projectile ammo into the corpse inventory, so the mod now checks corpse contents before adding recovery loot.
   - If intact bolts and broken bolts appear together for the same ammo type, delayed cleanup removes the broken duplicate.
   - Hit handler now guards nil ammo type.
   - Reload now queues repeated weapon field syncs after vanilla `loadAmmo()` for crossbows. This should prevent the multiplayer state where the server has loaded the bolt but the client still displays `0/1` until the weapon is dropped and picked up.

4. Crafting changes:
   - The old copied recipe file and its Lua `OnCreate` handlers were removed.
   - Only the new no-book survival recipe file remains active.
   - Fixed Build 42 recipe input syntax for assembled wood bolt recipes so the server no longer removes them at script load.
   - Removed the unused `BoltFletchings` intermediate item, model, textures, and recipe.
   - Wood bolt assembly now consumes rags/paper directly instead of crafting a separate fletching item.
   - Recipe, item, UI, and sandbox text was migrated to Build 42 JSON translation files.
   - English is the base language; Ukrainian has a complete override for players using the Ukrainian locale.
   - Hand crossbows now hold 4 bolts internally and use `WeaponReloadType = shotgun` without magazine items.
   - Hand crossbows do not use `InsertAllBulletsReload` or `ManuallyRemoveSpentRounds`; they follow the vanilla JS-2000 chamber/rack pattern with `RackAfterShoot = TRUE` and no forced `HaveChamber = FALSE`.
   - Hand crossbow muzzle attachments now use handgun/revolver-style `rotate = -90 0 0` so the projectile tracer follows the aim direction instead of the old sideways muzzle orientation.
   - Removed all stringless crossbow items and the Lua conversion that replaced broken crossbows with stringless variants.
   - Removed custom crossbow scope items; vanilla `Base.x2Scope`, `Base.x4Scope`, and `Base.x8Scope` are mountable on compound crossbow variants instead.
   - Removed old crossbow stock intermediate items, forage entries, models, textures, and translations because current recipes craft crossbows directly from raw materials.
   - Crossbow recipes moved to `Weaponry`; bolt shaft carving moved to `Carving`; bolt assembly moved to `Assembly`; stone bolt heads remain in `Knapping`.
   - Crossbow crafting balance pass:
     - crude crossbow remains the cheap forest-survival option but needs more binding,
     - hand crossbow needs more binding and one wire for the internal four-bolt feed mechanism,
     - improved crossbow now requires a plank, sticks, nails, saw, and binding,
     - compound crossbow now requires two planks, sticks, wire, nails, saw, and binding.
   - Removed unused alternate crossbow variants:
     - wire-string crossbows,
     - metal-bolt crossbows,
     - wire-string metal-bolt crossbows.
   - Removed metal bolt ammo, recovery sandbox options, translations, loot/forage entries, and unused IB drawn models/textures. Loot and foraging now point to the same four base crossbows used by crafting.
   - Added a small client patch for the vanilla character screen so `Favourite Weapon` shows the crossbow display name instead of the raw full type like `PZCrossbows.CompoundCrossBow`.
   - Removed large and short wood bolt stack items, models, textures, loot/forage entries, translations, and weapon `AmmoBox` references. Bolts are now handled only as individual items.
   - Survival skill gates:
     - crude crossbow: `Maintenance:1`,
     - hand and improved crossbows: `Maintenance:1;Woodwork:2`,
     - compound crossbow: `Maintenance:2;Woodwork:4`,
     - stone bolt heads: `FlintKnapping:1`,
     - bolt shafts and assembled bolts: `Carving:1`.
   - Active recipes cover:
     - wood bolt shafts,
     - short wood bolt shafts,
     - stone/bone bolt heads,
     - wood and short wood bolts,
     - crude, hand, improved, and compound crossbows.

## Next Development Steps

1. Test mod loading on Project Zomboid `42.19.0`.
2. Create a fresh save with only `PZCrossbows` enabled.
3. Verify all crossbows and ammo spawn through debug item list.
4. Shoot zombies with each ammo type and verify:
   - no `OnZombieDead` Lua errors,
   - corpse contains either intact or broken bolts for a type,
   - items can be picked up normally.
5. Tune recipe costs after real survival testing.
6. Replace temporary copied textures/models/sounds with original/redrawn assets.

## Notes

The current build prioritizes working mechanics over final authorship polish. It is the right base for testing, balancing, and then replacing art cleanly.
