require "TimedActions/ISBaseTimedAction"
require "TimedActions/ISReloadWeaponAction"
require "TimedActions/ISUnloadBulletsFromFirearm"
require "TimedActions/ISRackFirearm"

PZCrossbowsAmmo = PZCrossbowsAmmo or {}

PZCrossbowsAmmo.CrossbowTypes = {
	["PZCrossbows.Crossbow"] = true,
	["PZCrossbows.ImprovedCrossBow"] = true,
	["PZCrossbows.CompoundCrossBow"] = true,
	["PZCrossbows.HandCrossBow"] = true,
}

PZCrossbowsAmmo.Config = {
	Crossbow = {
		wood = {
			ammoId = "pzcrossbows:wood_bolt",
			itemKey = "PZCrossbows.WoodBolt",
			minDamage = 0.6,
			maxDamage = 1.1,
			critChance = 20,
			doorDamage = 8,
			icon = "media/textures/Item_WoodBolt.png",
		},
		metal = {
			ammoId = "pzcrossbows:metal_bolt",
			itemKey = "PZCrossbows.MetalBolt",
			minDamage = 0.8,
			maxDamage = 1.4,
			critChance = 30,
			doorDamage = 12,
			icon = "media/textures/Item_MetalBolt.png",
		},
	},
	ImprovedCrossBow = {
		wood = {
			ammoId = "pzcrossbows:wood_bolt",
			itemKey = "PZCrossbows.WoodBolt",
			minDamage = 0.8,
			maxDamage = 1.2,
			critChance = 25,
			doorDamage = 8,
			icon = "media/textures/Item_WoodBolt.png",
		},
		metal = {
			ammoId = "pzcrossbows:metal_bolt",
			itemKey = "PZCrossbows.MetalBolt",
			minDamage = 1.05,
			maxDamage = 1.55,
			critChance = 35,
			doorDamage = 12,
			icon = "media/textures/Item_MetalBolt.png",
		},
	},
	CompoundCrossBow = {
		wood = {
			ammoId = "pzcrossbows:wood_bolt",
			itemKey = "PZCrossbows.WoodBolt",
			minDamage = 1.25,
			maxDamage = 1.5,
			critChance = 30,
			doorDamage = 10,
			icon = "media/textures/Item_WoodBolt.png",
		},
		metal = {
			ammoId = "pzcrossbows:metal_bolt",
			itemKey = "PZCrossbows.MetalBolt",
			minDamage = 1.6,
			maxDamage = 1.95,
			critChance = 40,
			doorDamage = 15,
			icon = "media/textures/Item_MetalBolt.png",
		},
	},
	HandCrossBow = {
		wood = {
			ammoId = "pzcrossbows:short_wood_bolt",
			itemKey = "PZCrossbows.ShortWoodBolt",
			minDamage = 0.6,
			maxDamage = 0.9,
			critChance = 20,
			doorDamage = 8,
			icon = "media/textures/Item_ShortWoodBolt.png",
		},
		metal = {
			ammoId = "pzcrossbows:short_metal_bolt",
			itemKey = "PZCrossbows.ShortMetalBolt",
			minDamage = 0.8,
			maxDamage = 1.2,
			critChance = 30,
			doorDamage = 10,
			icon = "media/textures/Item_ShortMetalBolt.png",
		},
	},
}

function PZCrossbowsAmmo.isCrossbow(weapon)
	if not weapon or not weapon.getFullType then return false end
	return PZCrossbowsAmmo.CrossbowTypes[weapon:getFullType()] == true
end

function PZCrossbowsAmmo.getWeaponConfig(weapon)
	if not weapon or not weapon.getType then return nil end
	return PZCrossbowsAmmo.Config[weapon:getType()]
end

function PZCrossbowsAmmo.getAmmoTypeObj(ammoId)
	if not ammoId then return nil end
	if AmmoType and AmmoType.get and ResourceLocation and ResourceLocation.of then
		local ok, res = pcall(function()
			return AmmoType.get(ResourceLocation.of(ammoId))
		end)
		if ok and res then
			return res
		end
	end
	return nil
end

function PZCrossbowsAmmo.getKind(weapon)
	if not weapon then return "wood" end
	local modData = weapon:getModData()
	if modData and (modData.PZC_AmmoKind == "metal" or modData.PZC_AmmoKind == "wood") then
		return modData.PZC_AmmoKind
	end
	local ammoType = weapon:getAmmoType()
	if ammoType then
		local str = tostring(ammoType:toString())
		local itemKey = ammoType.getItemKey and ammoType:getItemKey() or ""
		if str == "pzcrossbows:metal_bolt" or str == "pzcrossbows:short_metal_bolt"
			or itemKey == "PZCrossbows.MetalBolt" or itemKey == "PZCrossbows.ShortMetalBolt" then
			return "metal"
		end
	end
	return "wood"
end

function PZCrossbowsAmmo.getAltKind(kind)
	return (kind == "metal") and "wood" or "metal"
end

function PZCrossbowsAmmo.applyAmmoKind(weapon, kind, characterToSync)
	local cfg = PZCrossbowsAmmo.getWeaponConfig(weapon)
	if not cfg then return false end
	local normKind = (kind == "metal") and "metal" or "wood"
	local entry = cfg[normKind]
	if not entry then return false end

	local modData = weapon:getModData()
	if modData then
		modData.PZC_AmmoKind = normKind
	end

	local ammoTypeObj = PZCrossbowsAmmo.getAmmoTypeObj(entry.ammoId)
	if ammoTypeObj then
		weapon:setAmmoType(ammoTypeObj)
	end
	weapon:setMinDamage(entry.minDamage)
	weapon:setMaxDamage(entry.maxDamage)
	weapon:setCriticalChance(entry.critChance)
	weapon:setDoorDamage(entry.doorDamage)

	if characterToSync and (not isClient or not isClient()) then
		if syncItemFields then
			syncItemFields(characterToSync, weapon)
		end
		if syncHandWeaponFields then
			syncHandWeaponFields(characterToSync, weapon)
		end
	end
	return true
end

function PZCrossbowsAmmo.ensureSynced(weapon)
	local cfg = PZCrossbowsAmmo.getWeaponConfig(weapon)
	if not cfg then return false end
	local kind = PZCrossbowsAmmo.getKind(weapon)
	local entry = cfg[kind]
	if not entry then return false end

	local ammoTypeObj = PZCrossbowsAmmo.getAmmoTypeObj(entry.ammoId)
	local modData = weapon:getModData()
	local needsUpdate = false

	if modData and modData.PZC_AmmoKind ~= kind then
		needsUpdate = true
	elseif ammoTypeObj and weapon:getAmmoType() ~= ammoTypeObj then
		needsUpdate = true
	elseif math.abs(weapon:getMinDamage() - entry.minDamage) > 0.001 then
		needsUpdate = true
	elseif math.abs(weapon:getMaxDamage() - entry.maxDamage) > 0.001 then
		needsUpdate = true
	elseif math.abs(weapon:getCriticalChance() - entry.critChance) > 0.001 then
		needsUpdate = true
	elseif weapon:getDoorDamage() ~= entry.doorDamage then
		needsUpdate = true
	end

	if needsUpdate then
		PZCrossbowsAmmo.applyAmmoKind(weapon, kind, nil)
	end
	return true
end

function PZCrossbowsAmmo.getKindForBoltItem(weapon, fullType)
	local cfg = PZCrossbowsAmmo.getWeaponConfig(weapon)
	if not cfg or not fullType then return nil end
	if cfg.wood and cfg.wood.itemKey == fullType then return "wood" end
	if cfg.metal and cfg.metal.itemKey == fullType then return "metal" end
	return nil
end

-- Net-compatible TimedAction to switch crossbow ammo type in exact queue sequence
ISPZCSwitchCrossbowAmmo = ISBaseTimedAction:derive("ISPZCSwitchCrossbowAmmo")

function ISPZCSwitchCrossbowAmmo:isValid()
	if isClient() and self.gun and self.character then
		self.gun = self.character:getInventory():getItemById(self.gun:getID()) or self.gun
	end
	return self.gun ~= nil and PZCrossbowsAmmo.isCrossbow(self.gun) and self.gun:getCurrentAmmoCount() == 0
end

function ISPZCSwitchCrossbowAmmo:start()
	if isClient() and self.gun and self.character then
		self.gun = self.character:getInventory():getItemById(self.gun:getID()) or self.gun
	end
	if self.gun and self.gun:getCurrentAmmoCount() == 0 then
		PZCrossbowsAmmo.applyAmmoKind(self.gun, self.ammoKind, nil)
	end
end

function ISPZCSwitchCrossbowAmmo:update()
end

function ISPZCSwitchCrossbowAmmo:stop()
	ISBaseTimedAction.stop(self)
end

function ISPZCSwitchCrossbowAmmo:serverStart()
	if self.gun and self.gun:getCurrentAmmoCount() == 0 then
		PZCrossbowsAmmo.applyAmmoKind(self.gun, self.ammoKind, self.character)
	end
end

function ISPZCSwitchCrossbowAmmo:getDuration()
	return 0
end

function ISPZCSwitchCrossbowAmmo:complete()
	if self.gun and self.gun:getCurrentAmmoCount() == 0 then
		PZCrossbowsAmmo.applyAmmoKind(self.gun, self.ammoKind, self.character)
	end
	return true
end

function ISPZCSwitchCrossbowAmmo:perform()
	if self.gun and self.gun:getCurrentAmmoCount() == 0 then
		PZCrossbowsAmmo.applyAmmoKind(self.gun, self.ammoKind, self.character)
	end
	ISBaseTimedAction.perform(self)
end

function ISPZCSwitchCrossbowAmmo:new(character, gun, ammoKind)
	local o = ISBaseTimedAction.new(self, character)
	o.gun = gun
	o.ammoKind = (ammoKind == "metal") and "metal" or "wood"
	o.stopOnWalk = false
	o.stopOnRun = false
	o.stopOnAim = false
	o.maxTime = o:getDuration()
	o.useProgressBar = false
	return o
end

-- Queue full unload (if needed) + ammo switch + transfer from bags/quiver + reload
function PZCrossbowsAmmo.queueSwitchAndReload(playerObj, gun, targetKind, equipFirst)
	if not playerObj or not gun then return false end
	local cfg = PZCrossbowsAmmo.getWeaponConfig(gun)
	if not cfg then return false end
	PZCrossbowsAmmo.ensureSynced(gun)

	local normKind = (targetKind == "metal") and "metal" or "wood"
	local targetEntry = cfg[normKind]
	if not targetEntry then return false end

	local inventory = playerObj:getInventory()
	if not inventory then return false end
	local avail = inventory:getItemCountRecurse(targetEntry.itemKey)
	if avail <= 0 then return false end

	if equipFirst and ISInventoryPaneContextMenu and ISInventoryPaneContextMenu.equipWeapon then
		ISInventoryPaneContextMenu.equipWeapon(gun, true, false, playerObj:getPlayerNum())
	end

	local currentKind = PZCrossbowsAmmo.getKind(gun)
	local currentAmmo = gun:getCurrentAmmoCount()

	if currentKind ~= normKind then
		if currentAmmo > 0 then
			ISTimedActionQueue.add(ISUnloadBulletsFromFirearm:new(playerObj, gun, false))
		else
			PZCrossbowsAmmo.applyAmmoKind(gun, normKind, playerObj)
		end
		ISTimedActionQueue.add(ISPZCSwitchCrossbowAmmo:new(playerObj, gun, normKind))
		if ISInventoryPaneContextMenu and ISInventoryPaneContextMenu.transferBullets then
			ISInventoryPaneContextMenu.transferBullets(playerObj, targetEntry.itemKey, 0, gun:getMaxAmmo())
		end
		ISTimedActionQueue.add(ISReloadWeaponAction:new(playerObj, gun))
		return true
	else
		if currentAmmo >= gun:getMaxAmmo() then
			return false
		end
		if ISInventoryPaneContextMenu and ISInventoryPaneContextMenu.transferBullets then
			local transferred = ISInventoryPaneContextMenu.transferBullets(playerObj, targetEntry.itemKey, currentAmmo, gun:getMaxAmmo())
			if transferred <= 0 then return false end
		end
		ISTimedActionQueue.add(ISReloadWeaponAction:new(playerObj, gun))
		return true
	end
end

-- 1. Quiver reload speed bonus
if not ISReloadWeaponAction.PZC_SetReloadSpeedPatched then
	local PZC_originalSetReloadSpeed = ISReloadWeaponAction.setReloadSpeed
	function ISReloadWeaponAction.setReloadSpeed(character, rack)
		PZC_originalSetReloadSpeed(character, rack)

		local gun = character and character:getPrimaryHandItem()
		if not gun or not PZCrossbowsAmmo.isCrossbow(gun) then
			return
		end

		local quiver = character:getWornItem(ItemBodyLocation.AMMO_STRAP)
		if quiver and quiver:getFullType() == "PZCrossbows.BoltQuiver" then
			local speed = character:getVariableFloat("ReloadSpeed", 1.0)
			character:setVariable("ReloadSpeed", speed * 1.15)
		end
	end
	ISReloadWeaponAction.PZC_SetReloadSpeedPatched = true
end

-- 2. Automatic reload ('R' key / controller RBumper) with recursive search & auto-unload/switch
if not ISReloadWeaponAction.PZC_BeginAutomaticReloadPatched then
	local PZC_originalBeginAutomaticReload = ISReloadWeaponAction.BeginAutomaticReload
	function ISReloadWeaponAction.BeginAutomaticReload(playerObj, gun)
		if gun and PZCrossbowsAmmo.isCrossbow(gun) then
			PZCrossbowsAmmo.ensureSynced(gun)
			if gun:isJammed() then return end
			if gun:getCurrentAmmoCount() >= gun:getMaxAmmo() then return end

			local cfg = PZCrossbowsAmmo.getWeaponConfig(gun)
			if not cfg then return end
			local currentKind = PZCrossbowsAmmo.getKind(gun)
			local altKind = PZCrossbowsAmmo.getAltKind(currentKind)
			local currentEntry = cfg[currentKind]
			local altEntry = cfg[altKind]

			local inv = playerObj and playerObj:getInventory()
			if not inv then return end

			local currentAvail = currentEntry and inv:getItemCountRecurse(currentEntry.itemKey) or 0
			if currentAvail > 0 then
				PZCrossbowsAmmo.queueSwitchAndReload(playerObj, gun, currentKind, false)
				return
			end

			local altAvail = altEntry and inv:getItemCountRecurse(altEntry.itemKey) or 0
			if altAvail > 0 then
				PZCrossbowsAmmo.queueSwitchAndReload(playerObj, gun, altKind, false)
				return
			end
			return
		end
		return PZC_originalBeginAutomaticReload(playerObj, gun)
	end
	ISReloadWeaponAction.PZC_BeginAutomaticReloadPatched = true
end

-- 3. Ensure ISReloadWeaponAction:initVars() syncs ammo kind on both client & server
if not ISReloadWeaponAction.PZC_InitVarsPatched then
	local PZC_originalInitVars = ISReloadWeaponAction.initVars
	function ISReloadWeaponAction:initVars()
		if self.gun and PZCrossbowsAmmo.isCrossbow(self.gun) then
			PZCrossbowsAmmo.ensureSynced(self.gun)
			if self.gun:getCurrentAmmoCount() == 0 and self.character then
				local cfg = PZCrossbowsAmmo.getWeaponConfig(self.gun)
				local inv = self.character:getInventory()
				if cfg and inv then
					local curKind = PZCrossbowsAmmo.getKind(self.gun)
					local altKind = PZCrossbowsAmmo.getAltKind(curKind)
					if inv:getItemCountRecurse(cfg[curKind].itemKey) == 0 and inv:getItemCountRecurse(cfg[altKind].itemKey) > 0 then
						PZCrossbowsAmmo.applyAmmoKind(self.gun, altKind, self.character)
					end
				end
			end
		end
		PZC_originalInitVars(self)
	end

	local PZC_originalLoadAmmo = ISReloadWeaponAction.loadAmmo
	if PZC_originalLoadAmmo then
		function ISReloadWeaponAction:loadAmmo()
			if self.gun and PZCrossbowsAmmo.isCrossbow(self.gun) then
				if self.bullets and not self.bullets:isEmpty() then
					local bullet = self.bullets:get(0)
					local bulletKind = bullet and PZCrossbowsAmmo.getKindForBoltItem(self.gun, bullet:getFullType())
					if bulletKind then
						PZCrossbowsAmmo.applyAmmoKind(self.gun, bulletKind, nil)
					else
						PZCrossbowsAmmo.ensureSynced(self.gun)
					end
				else
					PZCrossbowsAmmo.ensureSynced(self.gun)
				end
			end
			return PZC_originalLoadAmmo(self)
		end
	end
	ISReloadWeaponAction.PZC_InitVarsPatched = true
end

-- 4. Ensure Unload and Rack actions always sync the crossbow's current ammo type before ejecting bolts
if ISUnloadBulletsFromFirearm and not ISUnloadBulletsFromFirearm.PZC_SyncPatched then
	local PZC_origUnloadStart = ISUnloadBulletsFromFirearm.start
	function ISUnloadBulletsFromFirearm:start()
		if self.gun and PZCrossbowsAmmo.isCrossbow(self.gun) then
			PZCrossbowsAmmo.ensureSynced(self.gun)
		end
		PZC_origUnloadStart(self)
	end

	local PZC_origUnloadServerStart = ISUnloadBulletsFromFirearm.serverStart
	if PZC_origUnloadServerStart then
		function ISUnloadBulletsFromFirearm:serverStart()
			if self.gun and PZCrossbowsAmmo.isCrossbow(self.gun) then
				PZCrossbowsAmmo.ensureSynced(self.gun)
			end
			PZC_origUnloadServerStart(self)
		end
	end
	ISUnloadBulletsFromFirearm.PZC_SyncPatched = true
end

if ISRackFirearm and not ISRackFirearm.PZC_SyncPatched then
	local PZC_origRackStart = ISRackFirearm.start
	function ISRackFirearm:start()
		if self.gun and PZCrossbowsAmmo.isCrossbow(self.gun) then
			PZCrossbowsAmmo.ensureSynced(self.gun)
		end
		PZC_origRackStart(self)
	end

	local PZC_origRackServerStart = ISRackFirearm.serverStart
	if PZC_origRackServerStart then
		function ISRackFirearm:serverStart()
			if self.gun and PZCrossbowsAmmo.isCrossbow(self.gun) then
				PZCrossbowsAmmo.ensureSynced(self.gun)
			end
			PZC_origRackServerStart(self)
		end
	end
	ISRackFirearm.PZC_SyncPatched = true
end
