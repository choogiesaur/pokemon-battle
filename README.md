pokemon-battle
==============

Attempt at an accurate simulation of a 1v1 pokemon battle as a coding exercise, coded in **Python 2.7.6**.

----

If you run the python script from the zip, a battle simulation should be up with a bit implemented. 
It wont randomly generate anything other than the starter pokemon of you and the rival from and the levels of both your pokemon on your teams. 

To try out different team compositions, you could enter the pokemon id's of whatever pokemon you wanted inside the script itself.
IDs and names can be found [in the repo](pokemon%20data/pokemon.csv), or somewhere on the internet.

**Already implemented**:
- A basic menu for battling, swapping, and running with a pretty basic computer AI
- Skill accuracy, skill damage, skill priority, skill type efficacy (super effective, etc), skill PP tracking
- IVs, EVs, all skills the pokemon will learn, pokemon speed, experience, skill slots, leveling up, learning skills, natures (brave, bold, etc) and their effect on stats
- And maybe a few other things
 
**Notably missing**:
- Any skill that is a status change (tail whip, etc) will flat out be unable to be used
- Anything that has a secondary effect (takedown recoil damage, moves that have chance to posion, etc) wont work
- No items implementation at all (pokemon holding berries, using potions, etc)
- Innate pokemon abilities aren't in,
- Evolution (not too big of an issue for a single battle)
- And probably some other stuff.