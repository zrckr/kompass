extends Node

## Describes which side of triple can participate in the physical interaction
enum PhysicsLayer {
	NONE = 1,
	FACE_TOP,
	FACE_BOTTOM,
	FACE_LEFT,
	FACE_RIGHT,
	FACE_FRONT,
	FACE_BACK,
}

## Get entities directly, bypassing the fetching a node via [NodePath]
const Group = {
	PLAYER = &'player',
	NPC = &'npc',
}
