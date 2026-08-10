local PZCrossbowsDebug = false

local function PZCrossbowsSide()
	if isServer() then return "SERVER" end
	if isClient() then return "CLIENT" end
	return "SP"
end

local function PZCrossbowsDebugPrint(message)
	if not PZCrossbowsDebug then return end
	print("[PZCrossbows][" .. PZCrossbowsSide() .. "] " .. message)
end

local CrossbowItems = {
	"Crossbow",
	"ImprovedCrossBow",
	"CompoundCrossBow",
	"HandCrossBow",
}

local function CheckIsCrossbow(weapon)
	if not weapon then return false end
	for i = 1, #CrossbowItems do
		if weapon:getType() == CrossbowItems[i] then
			return true
		end
	end
	return false
end

local function PZCrossbowsClampRecoveryChance(value)
	value = tonumber(value) or 0
	if value < 0 then return 0 end
	if value > 100 then return 100 end
	return value
end

local function PZCrossbowsAddItemsToZombieInventory(zombie, itemType, count)
	local inventory = zombie and zombie:getInventory()
	if not inventory or not itemType then return end
	for i = 1, count do
		inventory:AddItem(itemType)
	end
end

local function PZCrossbowsGetItemCount(inventory, itemType)
	if not inventory or not itemType then return 0 end
	local items = inventory:getItemsFromFullType(itemType)
	if not items then return 0 end
	return items:size()
end

local function PZCrossbowsRemoveItemsByType(inventory, itemType)
	if not inventory or not itemType then return end
	local items = inventory:getItemsFromFullType(itemType)
	if not items then return end
	for i = items:size() - 1, 0, -1 do
		local item = items:get(i)
		if item then
			inventory:DoRemoveItem(item)
		end
	end
end

local PZCrossbowsBoltPairs = {
	{ intact = "PZCrossbows.WoodBolt", broken = "PZCrossbows.BrokenBolt" },
	{ intact = "PZCrossbows.ShortWoodBolt", broken = "PZCrossbows.BrokenShortBolt" },
}

local function PZCrossbowsCleanupCorpseBoltDuplicates(zombie)
	local inventory = zombie and zombie:getInventory()
	if not inventory then return end
	for i = 1, #PZCrossbowsBoltPairs do
		local pair = PZCrossbowsBoltPairs[i]
		if PZCrossbowsGetItemCount(inventory, pair.intact) > 0 then
			PZCrossbowsRemoveItemsByType(inventory, pair.broken)
		end
	end
end

local function PZCrossbowsRecoverBoltBatch(zombie, modData, countKey, spawnedKey, intactItem, brokenItem, baseChance, scaling)
	local count = tonumber(modData[countKey]) or 0
	if count <= 0 or modData[spawnedKey] == true then return end
	local inventory = zombie and zombie:getInventory()
	if not inventory then return end
	if PZCrossbowsGetItemCount(inventory, intactItem) > 0 then
		PZCrossbowsRemoveItemsByType(inventory, brokenItem)
		modData[countKey] = 0
		modData[spawnedKey] = true
		return
	end
	if PZCrossbowsGetItemCount(inventory, brokenItem) > 0 then
		modData[countKey] = 0
		modData[spawnedKey] = true
		return
	end
	local maintenanceLevel = tonumber(modData.MaintenanceLevel) or 0
	local recoveryChance = PZCrossbowsClampRecoveryChance((tonumber(baseChance) or 0) + maintenanceLevel * (tonumber(scaling) or 0))
	local itemType = brokenItem
	if ZombRand(1, 100) <= recoveryChance then
		itemType = intactItem
	end
	PZCrossbowsAddItemsToZombieInventory(zombie, itemType, count)
	modData[countKey] = 0
	modData[spawnedKey] = true
end

-- Bolt recovery is server authoritative. Without this guard a multiplayer client
-- runs the whole batch a second time with its own ZombRand roll, so the two sides
-- can disagree on intact vs broken and the corpse ends up with duplicates.
local function PZCrossbowsOnZombieDead(zombie)
	if isClient() then return end
	if not zombie then return end
	local modData = zombie:getModData()
	if not modData then return end
	local vars = SandboxVars and SandboxVars.PZCrossbows
	if not vars then return end
	PZCrossbowsRecoverBoltBatch(zombie, modData, "BoltNumW", "WSpawned", "PZCrossbows.WoodBolt", "PZCrossbows.BrokenBolt", vars.BoltWBaseBreakChance, vars.BoltWBreakChanceScaling)
	PZCrossbowsRecoverBoltBatch(zombie, modData, "BoltNumSW", "SWSpawned", "PZCrossbows.ShortWoodBolt", "PZCrossbows.BrokenShortBolt", vars.BoltSWBaseBreakChance, vars.BoltSWBreakChanceScaling)
	PZCrossbowsCleanupCorpseBoltDuplicates(zombie)
end

local function PZCrossbowsHitCrossbow(attacker, target, weapon, damage)
	if isClient() then return end
	if not CheckIsCrossbow(weapon) then return end
	local ammoTypeObj = weapon:getAmmoType()
	if not ammoTypeObj then return end
	local ammoType = ammoTypeObj:toString()
	local modData = target:getModData()
	if ammoType == "pzcrossbows:wood_bolt" then
		modData.BoltNumW = (tonumber(modData.BoltNumW) or 0) + 1
		modData.MaintenanceLevel = attacker:getPerkLevel(Perks.Maintenance)
		modData.WSpawned = false
	elseif ammoType == "pzcrossbows:short_wood_bolt" then
		modData.BoltNumSW = (tonumber(modData.BoltNumSW) or 0) + 1
		modData.MaintenanceLevel = attacker:getPerkLevel(Perks.Maintenance)
		modData.SWSpawned = false
	end
end

if ISReloadWeaponAction and ISReloadWeaponAction.loadAmmo and not ISReloadWeaponAction.PZCrossbowsLoadAmmoPatched then
	local PZCrossbowsOriginalLoadAmmo = ISReloadWeaponAction.loadAmmo
	ISReloadWeaponAction.loadAmmo = function(self)
		PZCrossbowsOriginalLoadAmmo(self)
		if self and self.gun and CheckIsCrossbow(self.gun) then
			syncItemFields(self.character, self.gun)
			syncHandWeaponFields(self.character, self.gun)
		end
	end
	ISReloadWeaponAction.PZCrossbowsLoadAmmoPatched = true
end

local PZCrossbowsModels = {
	Crossbow = {
		empty = { sprite = "PZCrossbows.CrossBow", texture = "media/textures/Item_CrossBow.png" },
		drawn = { sprite = "PZCrossbows.CrossBowDrawn", texture = "media/textures/Item_CrossBowDrawn.png" },
	},
	ImprovedCrossBow = {
		empty = { sprite = "PZCrossbows.ImprovedCrossBow", texture = "media/textures/Item_ImprovedCrossBow.png" },
		drawn = { sprite = "PZCrossbows.ImprovedCrossBowDrawn", texture = "media/textures/Item_ImprovedCrossBowDrawn.png" },
	},
	CompoundCrossBow = {
		empty = { sprite = "PZCrossbows.CompoundCrossBow", texture = "media/textures/Item_CompoundCrossBow.png" },
		drawn = { sprite = "PZCrossbows.CompoundCrossBowDrawn", texture = "media/textures/Item_CompoundCrossBowDrawn.png" },
	},
	HandCrossBow = {
		empty = { sprite = "PZCrossbows.HandCrossBow", texture = "media/textures/Item_HandCrossBow.png" },
		drawn = { sprite = "PZCrossbows.HandCrossBowDrawn", texture = "media/textures/Item_HandCrossBowDrawn.png" },
	},
}

-- The wanted sprite is derived from the weapon itself every update, so no state is
-- kept between players or between weapons. resetEquippedHandsModels() only runs on
-- the frame the sprite actually changes.
local function PZCrossbowsOnPlayerUpdate(player)
	local weapon = player:getPrimaryHandItem()
	if weapon == nil then return end
	local models = PZCrossbowsModels[weapon:getType()]
	if models == nil then return end
	local wanted = models.empty
	if weapon:getCurrentAmmoCount() > 0 then
		wanted = models.drawn
	end
	if weapon:getWeaponSprite() == wanted.sprite then return end
	weapon:setWeaponSprite(wanted.sprite)
	local texture = getTexture(wanted.texture)
	if texture then
		weapon:setTexture(texture)
	end
	player:resetEquippedHandsModels()
end

PZCrossbowsDebugPrint("zPZCrossbowsClient.lua loaded")

Events.OnPlayerUpdate.Add(PZCrossbowsOnPlayerUpdate)
Events.OnZombieDead.Add(PZCrossbowsOnZombieDead)
Events.OnWeaponHitCharacter.Add(PZCrossbowsHitCrossbow)
