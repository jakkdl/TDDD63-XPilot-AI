def åktill(målX,målY):
	
	MålVinkel=tan(((målX+ai.selfX())/(målY+ai.selfx()))

	Målvinkel=int(målvinkel)

	EgenVinkel=int(selfHeadingDeg())

	skillnadVinkel=angleDiff(Egenvinkel,Målvinkel)

	skillnadX=(ai.selfx())-målX

	skillnadY=int(ai.selfy())-målY

	if skillnadX<6 and skllnadY<6:

		pass

	elif skillnadX<11 and skillnadY<11:

		ai.thrust(0)

	elif skillnadVinkel<5:
		
		ai.thrust(1)

	else:
		
		ai.turn(skillnadVinkel)
	
	
		
	
	
