require "TimedActions/zPZCrossbowsReloadSpeed"
require "ISUI/ISFirearmRadialMenu"
require "ISUI/ISInventoryPaneContextMenu"
require "ISUI/ISToolTipInv"
pcall(require, "Entity/ISUI/Controls/ISItemSlot")

local function PZC_GetBoltDisplayName(itemKey)
	if getItemDisplayName then
		local name = getItemDisplayName(itemKey)
		if name and name ~= "" then return name end
	end
	if getScriptManager then
		local scriptItem = getScriptManager():FindItem(itemKey)
		if scriptItem then return scriptItem:getDisplayName() end
	end
	return itemKey
end

-- 1. Firearm Radial Menu (Hold 'R'): add slice to switch & load the alternate bolt type
if ISFirearmRadialMenu and not ISFirearmRadialMenu.PZC_AmmoRadialPatched then
	local PZC_origFillMenu = ISFirearmRadialMenu.fillMenu
	function ISFirearmRadialMenu:fillMenu()
		local weapon = self:getWeapon()
		if weapon and PZCrossbowsAmmo and PZCrossbowsAmmo.isCrossbow(weapon) then
			PZCrossbowsAmmo.ensureSynced(weapon)
		end

		PZC_origFillMenu(self)

		if not weapon or not PZCrossbowsAmmo or not PZCrossbowsAmmo.isCrossbow(weapon) then
			return
		end
		local cfg = PZCrossbowsAmmo.getWeaponConfig(weapon)
		if not cfg or not self.character then return end

		local currentKind = PZCrossbowsAmmo.getKind(weapon)
		local altKind = PZCrossbowsAmmo.getAltKind(currentKind)
		local altEntry = cfg[altKind]
		if not altEntry then return end

		local inv = self.character:getInventory()
		local altAvail = inv and inv:getItemCountRecurse(altEntry.itemKey) or 0
		if altAvail <= 0 then return end

		local menu = getPlayerRadialMenu(self.playerNum)
		if not menu then return end

		local boltName = PZC_GetBoltDisplayName(altEntry.itemKey)
		local label = getText("IGUI_FirearmRadial_PZCSwitchBolt", boltName) .. "\n(" .. tostring(altAvail) .. ")"
		local icon = getTexture(altEntry.icon) or getTexture("media/ui/FirearmRadial_BulletsIntoFirearm.png")

		menu:addSlice(label, icon, function()
			local wpn = self:getWeapon()
			if not wpn or not PZCrossbowsAmmo.isCrossbow(wpn) then return end
			PZCrossbowsAmmo.queueSwitchAndReload(self.character, wpn, altKind, false)
		end)
	end
	ISFirearmRadialMenu.PZC_AmmoRadialPatched = true
end

-- 2. Inventory Context Menu: allow loading/switching alternate bolt types on right-click
if ISInventoryPaneContextMenu and not ISInventoryPaneContextMenu.PZC_AmmoMenuPatched then
	local PZC_origDoReloadMenuForWeapon = ISInventoryPaneContextMenu.doReloadMenuForWeapon
	ISInventoryPaneContextMenu.doReloadMenuForWeapon = function(playerObj, weapon, context)
		if weapon and PZCrossbowsAmmo and PZCrossbowsAmmo.isCrossbow(weapon) then
			PZCrossbowsAmmo.ensureSynced(weapon)
		end
		PZC_origDoReloadMenuForWeapon(playerObj, weapon, context)

		if not weapon or not playerObj or not context or not PZCrossbowsAmmo or not PZCrossbowsAmmo.isCrossbow(weapon) then
			return
		end
		local cfg = PZCrossbowsAmmo.getWeaponConfig(weapon)
		if not cfg then return end

		local currentKind = PZCrossbowsAmmo.getKind(weapon)
		local altKind = PZCrossbowsAmmo.getAltKind(currentKind)
		local altEntry = cfg[altKind]
		if not altEntry then return end

		local inv = playerObj:getInventory()
		local altAvail = inv and inv:getItemCountRecurse(altEntry.itemKey) or 0
		if altAvail <= 0 then return end

		local countToLoad = math.min(altAvail, weapon:getMaxAmmo())
		local boltName = PZC_GetBoltDisplayName(altEntry.itemKey)
		context:addOption(
			getText("ContextMenu_InsertBullets", countToLoad, boltName, weapon:getDisplayName()),
			playerObj,
			PZCrossbowsAmmo.queueSwitchAndReload,
			weapon,
			altKind,
			true
		)
	end

	local PZC_origDoReloadMenuForBullets = ISInventoryPaneContextMenu.doReloadMenuForBullets
	ISInventoryPaneContextMenu.doReloadMenuForBullets = function(playerObj, bullet, context)
		if playerObj and PZCrossbowsAmmo then
			local items = playerObj:getInventory():getItems()
			for i = 0, items:size() - 1 do
				local item = items:get(i)
				if PZCrossbowsAmmo.isCrossbow(item) then
					PZCrossbowsAmmo.ensureSynced(item)
				end
			end
		end

		PZC_origDoReloadMenuForBullets(playerObj, bullet, context)

		if not playerObj or not bullet or not context or not PZCrossbowsAmmo then return end
		local bulletFullType = bullet:getFullType()
		local inv = playerObj:getInventory()
		local avail = inv:getItemCountRecurse(bulletFullType)
		if avail <= 0 then return end

		local items = inv:getItems()
		for i = 0, items:size() - 1 do
			local item = items:get(i)
			if PZCrossbowsAmmo.isCrossbow(item) then
				local targetKind = PZCrossbowsAmmo.getKindForBoltItem(item, bulletFullType)
				local currentKind = PZCrossbowsAmmo.getKind(item)
				if targetKind and targetKind ~= currentKind then
					local countToLoad = math.min(avail, item:getMaxAmmo())
					local boltName = PZC_GetBoltDisplayName(bulletFullType)
					context:addOption(
						getText("ContextMenu_InsertBullets", countToLoad, boltName, item:getDisplayName()),
						playerObj,
						PZCrossbowsAmmo.queueSwitchAndReload,
						item,
						targetKind,
						true
					)
				end
			end
		end
	end

	ISInventoryPaneContextMenu.PZC_AmmoMenuPatched = true
end

-- 3. Dynamic crossbow tooltip rendering:
-- HandWeapon.java caches `private String bulletName` the very first time DoTooltip runs and never clears it
-- when `setAmmoType` changes at runtime. We suppress only that stale cached row via temporary `setMaxAmmo(0)`
-- during `DoTooltipEmbedded` and append a live LayoutItem showing the active bolt's translated DisplayName.
local function PZC_DoCrossbowTooltip(weapon, tooltip)
	PZCrossbowsAmmo.ensureSynced(weapon)
	local cfg = PZCrossbowsAmmo.getWeaponConfig(weapon)
	if not cfg then
		weapon:DoTooltip(tooltip)
		return
	end

	local layout = tooltip:beginLayout()
	layout:setMinLabelWidth(80)
	layout:setMinValueWidth(80)

	local realMaxAmmo = weapon:getMaxAmmo()
	weapon:setMaxAmmo(0)
	local ok, err = pcall(function()
		weapon:DoTooltipEmbedded(tooltip, layout, 0)
	end)
	weapon:setMaxAmmo(realMaxAmmo)
	if not ok then
		tooltip:endLayout(layout)
		error(err)
	end

	if realMaxAmmo > 0 then
		local kind = PZCrossbowsAmmo.getKind(weapon)
		local entry = cfg[kind]
		local boltName = entry and PZC_GetBoltDisplayName(entry.itemKey) or ""
		local countStr = tostring(weapon:getCurrentAmmoCount())
		if weapon:isRoundChambered() then
			countStr = countStr .. "+1"
		end
		local boltItem = layout:addItem()
		boltItem:setLabel(boltName .. ":", 1.0, 1.0, 0.8, 1.0)
		boltItem:setValue(countStr .. "/" .. tostring(realMaxAmmo), 1.0, 1.0, 1.0, 1.0)
	end

	local font = tooltip:getFont()
	local charW = getTextManager():MeasureStringX(font, "0")
	local padLeft = charW
	local padTop = math.floor(charW / 2)
	local padBottom = padTop
	local lineSpacing = tooltip:getLineSpacing()
	local startY = padTop + lineSpacing + 5
	if weapon.getExtraItems then
		local extra = weapon:getExtraItems()
		if extra and not extra:isEmpty() then
			startY = startY + lineSpacing + 5
		end
	end

	local bottomY = layout:render(padLeft, startY, tooltip)
	tooltip:endLayout(layout)
	bottomY = bottomY + padBottom
	tooltip:setHeight(bottomY)
	if tooltip:getWidth() < 150 then
		tooltip:setWidth(150)
	end
end

if ISToolTipInv and ISToolTipInv.render and not ISToolTipInv.PZC_TooltipSyncPatched then
	local PZC_origTooltipRender = ISToolTipInv.render
	function ISToolTipInv:render()
		if not self.item or not PZCrossbowsAmmo or not PZCrossbowsAmmo.isCrossbow(self.item) then
			return PZC_origTooltipRender(self)
		end

		if ISContextMenu.instance and ISContextMenu.instance.visibleCheck then
			return
		end

		local mx = getMouseX() + 24
		local my = getMouseY() + 24
		if not self.followMouse then
			mx = self:getX()
			my = self:getY()
			if self.anchorBottomLeft then
				mx = self.anchorBottomLeft.x
				my = self.anchorBottomLeft.y
			end
		end

		local PADX = 0
		self.tooltip:setX(mx + PADX)
		self.tooltip:setY(my)

		self.tooltip:setWidth(50)
		self.tooltip:setMeasureOnly(true)
		PZC_DoCrossbowTooltip(self.item, self.tooltip)
		self.tooltip:setMeasureOnly(false)

		local myCore = getCore()
		local maxX = myCore:getScreenWidth()
		local maxY = myCore:getScreenHeight()

		local tw = self.tooltip:getWidth()
		local th = self.tooltip:getHeight()

		self.tooltip:setX(math.max(0, math.min(mx + PADX, maxX - tw - 1)))
		if not self.followMouse and self.anchorBottomLeft then
			self.tooltip:setY(math.max(0, math.min(my - th, maxY - th - 1)))
		else
			self.tooltip:setY(math.max(0, math.min(my, maxY - th - 1)))
		end

		if self.contextMenu and self.contextMenu.joyfocus then
			local playerNum = self.contextMenu.player
			self.tooltip:setX(getPlayerScreenLeft(playerNum) + 60)
			self.tooltip:setY(getPlayerScreenTop(playerNum) + 60)
		elseif self.contextMenu and self.contextMenu.currentOptionRect then
			if self.contextMenu.currentOptionRect.height > 32 then
				self:setY(my + self.contextMenu.currentOptionRect.height)
			end
			self:adjustPositionToAvoidOverlap(self.contextMenu.currentOptionRect)
		end

		self:setX(self.tooltip:getX() - PADX)
		self:setY(self.tooltip:getY())
		self:setWidth(tw + PADX)
		self:setHeight(th)

		if self.followMouse and (self.contextMenu == nil) then
			self:adjustPositionToAvoidOverlap({ x = mx - 24 * 2, y = my - 24 * 2, width = 24 * 2, height = 24 * 2 })
		end

		self:drawRect(0, 0, self.width, self.height, self.backgroundColor.a, self.backgroundColor.r, self.backgroundColor.g, self.backgroundColor.b)
		self:drawRectBorder(0, 0, self.width, self.height, self.borderColor.a, self.borderColor.r, self.borderColor.g, self.borderColor.b)
		PZC_DoCrossbowTooltip(self.item, self.tooltip)
	end
	ISToolTipInv.PZC_TooltipSyncPatched = true
end

if ISItemSlot and ISItemSlot.drawTooltip and not ISItemSlot.PZC_TooltipSyncPatched then
	local PZC_origItemSlotDrawTooltip = ISItemSlot.drawTooltip
	ISItemSlot.drawTooltip = function(_itemSlot, _tooltip)
		if _itemSlot and not _itemSlot.resource and _itemSlot.storedItem
			and PZCrossbowsAmmo and PZCrossbowsAmmo.isCrossbow(_itemSlot.storedItem) then
			PZC_DoCrossbowTooltip(_itemSlot.storedItem, _tooltip)
			return
		end
		return PZC_origItemSlotDrawTooltip(_itemSlot, _tooltip)
	end
	ISItemSlot.PZC_TooltipSyncPatched = true
end
