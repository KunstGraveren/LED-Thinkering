# ASTEROIDS WITH A CONSOLE CONTROLLER (XBOX360/PS4)

- demo_wled_controller_asteroids.py:

	- we have an spaceship (first + 2 pixels)
		- indicates lives (3 from the start)

	- asteroids are falling down in 4 colors (Blue,Yellow, Red, Green that matches the xbox controller colors X, Y, B, A)

	- we can shoot the asteroids (Blue,Yellow, Red, Green that matches the xbox controller colors X, Y, B, A) (xyab, ●■▲x)

	- if we shoot the wrong color, you lose a life, led strip will blink

	- if we dont shoot all the asteroids, and a asteroids hit the spaceship, you lose a life, led strip will blink

# FEATURES / ToDo:

- [x] Support multple console controllers
	- [x] ps4
	- [x] xbox360
  
- [] starting of the game
  - [] waiting until start button is pressed
	- [] xbox360 = xbox button
	- [] ps4 = ps button

- we want levels: 
  - we want to have groups of astoids falling down per level, a group consists of:
	  - xx astroids
		- from level x boss ?
		- 

	- with each level we want to:

	- per level we want
		- change speed
		- the number of asteroids

		- how the asteroids fall:
			- we want combo's
			- we want random time in between
   
   - max levels
     - = nr of leds - 3 lives - start pixel of astroids
   
   - how do we track levels / success of level:
     - spaceship move ahead by 1 pixel.
     - add a life for each 5 level
   
   - power ups / power charge ?
     - spaceship in difference color ?

- multiplayer ?

  - game to game talk, that is running on each pi
		- that translate into talking to the leds

	- when level is done, shoot/add those asteroids onto the other unit

- multiplayer - multi directions from here:
  - 1 pi2 - multiple controllers (players) (4usb ports)
    - 1 unit --> multiple led strings (3max)
    - multiple units --> 1 or more led strips

  - 2 pi's 
    - units --> each have there own string
