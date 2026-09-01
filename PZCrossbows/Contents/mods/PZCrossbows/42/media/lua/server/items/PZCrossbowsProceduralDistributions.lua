require 'Items/ProceduralDistributions'

local function setOrRemoveItem(itemsTable, itemType, weight)
	if not itemsTable or not itemType then return end
	local found = false
	for i = #itemsTable - 1, 1, -2 do
		if itemsTable[i] == itemType then
			if weight and weight > 0 then
				itemsTable[i + 1] = weight
				found = true
			else
				table.remove(itemsTable, i + 1)
				table.remove(itemsTable, i)
			end
		end
	end
	if not found and weight and weight > 0 then
		table.insert(itemsTable, itemType)
		table.insert(itemsTable, weight)
	end
end

local function PZCrossbowsUpdateDistributions()
	local vars = SandboxVars and SandboxVars.PZCrossbows
	local lootSpawnMult = (vars and vars.LootSpawnMult) or 1
	if lootSpawnMult < 0 then lootSpawnMult = 0 end

	local crudeMult = (vars and vars.CrudeCrossbowSpawnMult) or 1
	local improvedMult = (vars and vars.ImprovedCrossbowSpawnMult) or 1
	local compoundMult = (vars and vars.CompoundCrossbowSpawnMult) or 1
	local handMult = (vars and vars.HandCrossbowSpawnMult) or 1

	local crudeWeight = 4 * lootSpawnMult * crudeMult
	local improvedWeight = 6 * lootSpawnMult * improvedMult
	local compoundWeight = 8 * lootSpawnMult * compoundMult
	local handWeight = 6 * lootSpawnMult * handMult
	local quiverWeight = 6 * lootSpawnMult
	local woodBoltWeight = 20 * lootSpawnMult * compoundMult
	local shortWoodBoltWeight = 15 * lootSpawnMult * handMult

	local function updateCrossbows(listName, hasAmmo)
		local entry = ProceduralDistributions["list"] and ProceduralDistributions["list"][listName]
		if not entry or not entry.items then return end
		local items = entry.items
		setOrRemoveItem(items, "PZCrossbows.Crossbow", crudeWeight)
		setOrRemoveItem(items, "PZCrossbows.ImprovedCrossBow", improvedWeight)
		setOrRemoveItem(items, "PZCrossbows.CompoundCrossBow", compoundWeight)
		setOrRemoveItem(items, "PZCrossbows.HandCrossBow", handWeight)
		setOrRemoveItem(items, "PZCrossbows.BoltQuiver", quiverWeight)
		if hasAmmo then
			setOrRemoveItem(items, "PZCrossbows.WoodBoltBox", woodBoltWeight)
			setOrRemoveItem(items, "PZCrossbows.ShortWoodBoltBox", shortWoodBoltWeight)
		else
			setOrRemoveItem(items, "PZCrossbows.WoodBoltBox", 0)
			setOrRemoveItem(items, "PZCrossbows.ShortWoodBoltBox", 0)
		end
	end

	updateCrossbows("FirearmWeapons", true)
	updateCrossbows("FirearmWeapons_Mid", true)
	updateCrossbows("FirearmWeapons_Late", true)
	updateCrossbows("Hunter", false)
	updateCrossbows("GunStoreGuns", false)
	updateCrossbows("GunStoreRifles", false)
	updateCrossbows("BarCounterWeapon", true)

	local ammoList = ProceduralDistributions["list"] and ProceduralDistributions["list"]["GunStoreAmmunition"]
	if ammoList and ammoList.items then
		setOrRemoveItem(ammoList.items, "PZCrossbows.WoodBoltBox", woodBoltWeight)
		setOrRemoveItem(ammoList.items, "PZCrossbows.ShortWoodBoltBox", shortWoodBoltWeight)
	end

	local function updateRareCampingLoot(listName, baseWeight)
		local entry = ProceduralDistributions["list"] and ProceduralDistributions["list"][listName]
		if not entry or not entry.items then return end
		setOrRemoveItem(entry.items, "PZCrossbows.CompoundCrossBow", baseWeight * lootSpawnMult * compoundMult)
		setOrRemoveItem(entry.items, "PZCrossbows.BoltQuiver", baseWeight * lootSpawnMult)
	end

	updateRareCampingLoot("CampingStoreGear", 3)
	updateRareCampingLoot("CrateCamping", 0.12)
	updateRareCampingLoot("CampingLockers", 0.1)
	updateRareCampingLoot("WardrobeRedneck", 0.1)

	if IsoWorld and IsoWorld.parseDistributions then
		IsoWorld.parseDistributions()
	end
end

PZCrossbowsUpdateDistributions()

if Events.OnInitGlobalModData then
	Events.OnInitGlobalModData.Add(PZCrossbowsUpdateDistributions)
end
