# ASTEROIDS WITH A CONSOLE CONTROLLER (XBOX360/PS4)

## Objective: 
Shoot falling asteroids using your Xbox 360 or PS4 controller before they hit your spaceship. Avoid shooting the wrong colors and protect your ship to survive as long as possible.

## Controls:
- Start Game:
  	- Press the controller button (xbox/ps)
- Shoot Asteroids:
	- Press the controller buttons that match the asteroid colors:  
		- Xbox 360:  
			- X (Blue)  
			- Y (Yellow)  
			- B (Red)  
			- A (Green)

		- PS4:  
			- Cross (X) (Blue)  
			- Triangle (Y) (Yellow)  
			- Circle (B) (Red)  
			- Square (A) (Green)

Gameplay:

- The spaceship (represented by the first pixel + 2 pixels) starts with 3 lives.  
- Asteroids fall from the top in four colors: Blue, Yellow, Red, Green — matching the controller buttons X, Y, B, A respectively.  
- Shoot the asteroids by pressing the corresponding controller button when they are in reach.  
- Correct shots: Destroy the asteroid.  
- Wrong shots: Lose a life and see the LED strip blink to indicate mistake.  
- Missed asteroid hits: If an asteroid hits your spaceship without being shot, you lose a life, and the LED strip blinks.

# FEATURES / ToDo:

- [x] Support multple console controllers
	- [x] ps4
	- [x] xbox360

- [x] restart game if game over.
- [x] starting of the game
  - [x] waiting until start button is pressed
	- [x] xbox360 = xbox button
	- [x] ps4 = ps button

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
