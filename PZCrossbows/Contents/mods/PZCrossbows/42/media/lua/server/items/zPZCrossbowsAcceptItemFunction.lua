function AcceptItemFunction.PZC_BoltQuiver(container, item)
	local fullType = item:getFullType()
	return fullType == "PZCrossbows.WoodBolt"
		or fullType == "PZCrossbows.ShortWoodBolt"
		or fullType == "PZCrossbows.MetalBolt"
		or fullType == "PZCrossbows.ShortMetalBolt"
end
