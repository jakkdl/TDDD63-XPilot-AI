def �ktill(m�lX,m�lY):
	
	M�lVinkel=tan(((m�lX+ai.selfX())/(m�lY+ai.selfx()))

	M�lvinkel=int(m�lvinkel)

	EgenVinkel=int(selfHeadingDeg())

	skillnadVinkel=angleDiff(Egenvinkel,M�lvinkel)

	skillnadX=(ai.selfx())-m�lX

	skillnadY=int(ai.selfy())-m�lY

	if skillnadX<6 and skllnadY<6:

		pass

	elif skillnadX<11 and skillnadY<11:

		ai.thrust(0)

	elif skillnadVinkel<5:
		
		ai.thrust(1)

	else:
		
		ai.turn(skillnadVinkel)
	
	
		
	
	
