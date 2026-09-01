require "Definitions/AttachedWeaponDefinitions"

local function setOrRemoveAttachedWeapon(weaponsTable, itemType, enabled)
	if not weaponsTable or not itemType then return end
	local found = false
	for i = #weaponsTable, 1, -1 do
		if weaponsTable[i] == itemType then
			if enabled then
				found = true
			else
				table.remove(weaponsTable, i)
			end
		end
	end
	if enabled and not found then
		table.insert(weaponsTable, itemType)
	end
end

local function PZCrossbowsUpdateAttachedWeapons()
	local vars = SandboxVars and SandboxVars.PZCrossbows
	local lootSpawnMult = (vars and vars.LootSpawnMult) or 1
	local crudeMult = (vars and vars.CrudeCrossbowSpawnMult) or 1
	local improvedMult = (vars and vars.ImprovedCrossbowSpawnMult) or 1
	local compoundMult = (vars and vars.CompoundCrossbowSpawnMult) or 1
	local handMult = (vars and vars.HandCrossbowSpawnMult) or 1

	local crudeEnabled = (lootSpawnMult > 0) and (crudeMult > 0)
	local improvedEnabled = (lootSpawnMult > 0) and (improvedMult > 0)
	local compoundEnabled = (lootSpawnMult > 0) and (compoundMult > 0)
	local handEnabled = (lootSpawnMult > 0) and (handMult > 0)

	if AttachedWeaponDefinitions.gunOnBackMisc and AttachedWeaponDefinitions.gunOnBackMisc.weapons then
		setOrRemoveAttachedWeapon(AttachedWeaponDefinitions.gunOnBackMisc.weapons, "PZCrossbows.CompoundCrossBow", compoundEnabled)
		setOrRemoveAttachedWeapon(AttachedWeaponDefinitions.gunOnBackMisc.weapons, "PZCrossbows.ImprovedCrossBow", improvedEnabled)
	end
	if AttachedWeaponDefinitions.gunOnBackHunter and AttachedWeaponDefinitions.gunOnBackHunter.weapons then
		setOrRemoveAttachedWeapon(AttachedWeaponDefinitions.gunOnBackHunter.weapons, "PZCrossbows.CompoundCrossBow", compoundEnabled)
	end
	if AttachedWeaponDefinitions.gunOnBackBagSurvivalist and AttachedWeaponDefinitions.gunOnBackBagSurvivalist.weapons then
		setOrRemoveAttachedWeapon(AttachedWeaponDefinitions.gunOnBackBagSurvivalist.weapons, "PZCrossbows.CompoundCrossBow", compoundEnabled)
		setOrRemoveAttachedWeapon(AttachedWeaponDefinitions.gunOnBackBagSurvivalist.weapons, "PZCrossbows.ImprovedCrossBow", improvedEnabled)
		setOrRemoveAttachedWeapon(AttachedWeaponDefinitions.gunOnBackBagSurvivalist.weapons, "PZCrossbows.Crossbow", crudeEnabled)
	end
	if AttachedWeaponDefinitions.rifleOnBackGhillie and AttachedWeaponDefinitions.rifleOnBackGhillie.weapons then
		setOrRemoveAttachedWeapon(AttachedWeaponDefinitions.rifleOnBackGhillie.weapons, "PZCrossbows.CompoundCrossBow", compoundEnabled)
	end
	if AttachedWeaponDefinitions.meleeInBack_Early and AttachedWeaponDefinitions.meleeInBack_Early.weapons then
		setOrRemoveAttachedWeapon(AttachedWeaponDefinitions.meleeInBack_Early.weapons, "PZCrossbows.Crossbow", crudeEnabled)
	end
	if AttachedWeaponDefinitions.meleeInBack_Mid and AttachedWeaponDefinitions.meleeInBack_Mid.weapons then
		setOrRemoveAttachedWeapon(AttachedWeaponDefinitions.meleeInBack_Mid.weapons, "PZCrossbows.Crossbow", crudeEnabled)
		setOrRemoveAttachedWeapon(AttachedWeaponDefinitions.meleeInBack_Mid.weapons, "PZCrossbows.CompoundCrossBow", compoundEnabled)
	end
	if AttachedWeaponDefinitions.meleeInBack_Late and AttachedWeaponDefinitions.meleeInBack_Late.weapons then
		setOrRemoveAttachedWeapon(AttachedWeaponDefinitions.meleeInBack_Late.weapons, "PZCrossbows.ImprovedCrossBow", improvedEnabled)
		setOrRemoveAttachedWeapon(AttachedWeaponDefinitions.meleeInBack_Late.weapons, "PZCrossbows.CompoundCrossBow", compoundEnabled)
	end
	if AttachedWeaponDefinitions.meleeInBackBag and AttachedWeaponDefinitions.meleeInBackBag.weapons then
		setOrRemoveAttachedWeapon(AttachedWeaponDefinitions.meleeInBackBag.weapons, "PZCrossbows.Crossbow", crudeEnabled)
	end
	if AttachedWeaponDefinitions.meleeInBackBag_Mid and AttachedWeaponDefinitions.meleeInBackBag_Mid.weapons then
		setOrRemoveAttachedWeapon(AttachedWeaponDefinitions.meleeInBackBag_Mid.weapons, "PZCrossbows.Crossbow", crudeEnabled)
		setOrRemoveAttachedWeapon(AttachedWeaponDefinitions.meleeInBackBag_Mid.weapons, "PZCrossbows.CompoundCrossBow", compoundEnabled)
	end
	if AttachedWeaponDefinitions.meleeInBackBag_Late and AttachedWeaponDefinitions.meleeInBackBag_Late.weapons then
		setOrRemoveAttachedWeapon(AttachedWeaponDefinitions.meleeInBackBag_Late.weapons, "PZCrossbows.ImprovedCrossBow", improvedEnabled)
		setOrRemoveAttachedWeapon(AttachedWeaponDefinitions.meleeInBackBag_Late.weapons, "PZCrossbows.CompoundCrossBow", compoundEnabled)
	end
	if AttachedWeaponDefinitions.handgunHolster and AttachedWeaponDefinitions.handgunHolster.weapons then
		setOrRemoveAttachedWeapon(AttachedWeaponDefinitions.handgunHolster.weapons, "PZCrossbows.HandCrossBow", handEnabled)
	end
end

PZCrossbowsUpdateAttachedWeapons()

if Events.OnInitGlobalModData then
	Events.OnInitGlobalModData.Add(PZCrossbowsUpdateAttachedWeapons)
end
