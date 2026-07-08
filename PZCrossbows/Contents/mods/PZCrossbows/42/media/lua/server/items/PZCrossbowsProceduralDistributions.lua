require 'Items/ProceduralDistributions'

-- Standard weight per tier, in the same range vanilla uses for common guns (4-10).
-- Each is scaled by that tier's own sandbox multiplier, so 1.0 = this normal rate
-- and lowering the slider below 1.0 makes that tier rarer than a normal gun.
local CRUDE_WEIGHT = 4 * SandboxVars.PZCrossbows.CrudeCrossbowSpawnMult
local IMPROVED_WEIGHT = 6 * SandboxVars.PZCrossbows.ImprovedCrossbowSpawnMult
local COMPOUND_WEIGHT = 8 * SandboxVars.PZCrossbows.CompoundCrossbowSpawnMult
local HAND_WEIGHT = 6 * SandboxVars.PZCrossbows.HandCrossbowSpawnMult
-- These spawn as WoodBoltBox/ShortWoodBoltBox (a box of 10), matching how
-- vanilla ammo always spawns as a boxed stack rather than loose rounds.
local WOODBOLT_WEIGHT = 20 * SandboxVars.PZCrossbows.CompoundCrossbowSpawnMult
local SHORTWOODBOLT_WEIGHT = 15 * SandboxVars.PZCrossbows.HandCrossbowSpawnMult

-- Adds all 4 crossbow tiers to a list, so a location never offers only one
-- size/tier of crossbow (mirrors vanilla always offering full+sawnoff shotgun
-- together, full gun roster in FirearmWeapons_Mid/Late, etc). Pass hasAmmo=true
-- for lists that aren't flagged dontSpawnAmmo, to also add both bolt types.
local function addCrossbows(listName, hasAmmo)
	local items = ProceduralDistributions["list"][listName].items
	table.insert(items, "PZCrossbows.Crossbow")
	table.insert(items, CRUDE_WEIGHT)
	table.insert(items, "PZCrossbows.ImprovedCrossBow")
	table.insert(items, IMPROVED_WEIGHT)
	table.insert(items, "PZCrossbows.CompoundCrossBow")
	table.insert(items, COMPOUND_WEIGHT)
	table.insert(items, "PZCrossbows.HandCrossBow")
	table.insert(items, HAND_WEIGHT)
	if hasAmmo then
		table.insert(items, "PZCrossbows.WoodBoltBox")
		table.insert(items, WOODBOLT_WEIGHT)
		table.insert(items, "PZCrossbows.ShortWoodBoltBox")
		table.insert(items, SHORTWOODBOLT_WEIGHT)
	end
end

-- Survivor safehouse/cache loot (vanilla uses the identical gun roster across
-- all three of these, just with different roll counts - do the same here).
addCrossbows("FirearmWeapons", true)
addCrossbows("FirearmWeapons_Mid", true)
addCrossbows("FirearmWeapons_Late", true)

-- Ordinary houses: closets, garages, living rooms, storage units.
addCrossbows("Hunter", false)

-- Pawn Shop weapon racks/lockers (pawnshopoffice room).
addCrossbows("GunStoreGuns", false)

-- Rifle rack/display case (gunstore, hunting store, army surplus rooms).
addCrossbows("GunStoreRifles", false)

-- "Gun under the bar counter" slot - vanilla already mixes full-size and
-- sawnoff shotguns here, so every crossbow size belongs too.
addCrossbows("BarCounterWeapon", true)

-- Ammo shelves/lockers (pawn shop, gun store, hunting store, army surplus -
-- civilian rooms only, verified against Distributions.lua).
table.insert(ProceduralDistributions["list"]["GunStoreAmmunition"].items, "PZCrossbows.WoodBoltBox")
table.insert(ProceduralDistributions["list"]["GunStoreAmmunition"].items, WOODBOLT_WEIGHT)
table.insert(ProceduralDistributions["list"]["GunStoreAmmunition"].items, "PZCrossbows.ShortWoodBoltBox")
table.insert(ProceduralDistributions["list"]["GunStoreAmmunition"].items, SHORTWOODBOLT_WEIGHT)

-- Rare bonus finds in general storage (unchanged from before - these lists
-- have no other guns in them at all, so they stay a single rare surprise item
-- rather than a full weapon roster).
table.insert(ProceduralDistributions["list"]["CampingStoreGear"].items, "PZCrossbows.CompoundCrossBow")
table.insert(ProceduralDistributions["list"]["CampingStoreGear"].items, 3 * SandboxVars.PZCrossbows.CompoundCrossbowSpawnMult)
table.insert(ProceduralDistributions["list"]["CrateCamping"].items, "PZCrossbows.CompoundCrossBow")
table.insert(ProceduralDistributions["list"]["CrateCamping"].items, 0.12 * SandboxVars.PZCrossbows.CompoundCrossbowSpawnMult)
table.insert(ProceduralDistributions["list"]["CampingLockers"].items, "PZCrossbows.CompoundCrossBow")
table.insert(ProceduralDistributions["list"]["CampingLockers"].items, 0.1 * SandboxVars.PZCrossbows.CompoundCrossbowSpawnMult)
table.insert(ProceduralDistributions["list"]["WardrobeRedneck"].items, "PZCrossbows.CompoundCrossBow")
table.insert(ProceduralDistributions["list"]["WardrobeRedneck"].items, 0.1 * SandboxVars.PZCrossbows.CompoundCrossbowSpawnMult)
