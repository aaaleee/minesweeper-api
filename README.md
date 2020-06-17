### Minesweeper API

This is a small REST API for Minesweeper, the old game with the board and exploding mines. 

It was developed using Flask, SQLAlchemy, SQLite3, Swagger (for API docs), and a couple of other modules like pytest and marshmallow

It accepts and responds with json data. 

For auth it uses JWT.

I implemented a small command line version of minesweeper before starting with the API, it took me about 2/3 hours.


#### Things implemented so far:

- A small Javascript client module: https://github.com/aaaleee/minesweeper-js/blob/master/minesweeper.js
- When a cell with no adjacent mines is revealed, all adjacent squares will be revealed (and repeat)
- Ability to 'flag' a cell with a question mark or red flag. Flags are protected from clicking, question marks aren't as per the original implementation;
- Detect when game is over
- Persistence
- Time tracking in the form of start and end timestamps (could be improved to just indicate time taken).
- Ability to start a new game and preserve/resume the old ones
- Ability to select the game parameters: number of rows, columns, and mines (available through the API and the client library but not on the demo frontend).
- Ability to support multiple users/accounts

The API server runs on a micro EC2 instance at http://18.191.41.216:5000

To check the swagger json spec you can hit http://18.191.41.216:5000/spec

You can interact with the API through a very barebones js implementation here: http://18.191.41.216:8080/sample.html

There's a small http server and an API server both kept running using PM2 https://pm2.keymetrics.io/



#### What I would have done with more time

- Use alembic for schema migrations, not needed for now but if any data structures need to change having something to handle migrations becomes fundamental.
- More test coverage. Also, for this I tested some private methods in the game service, this was a quick workaround to eliminate the inherent randomness of the game from my testing but not really a pretty thing to see.
- A not so barebones client lib and frontend using Vue.js
- Separate API routes in flask blueprints. Not really necessary for this small project but nice to have.
- Add Swagger UI.
- Replace SQLite with either a NoSQL solution or a more scalable DB engine like Postgres.
- Improve the error messages a bit.
- Some refactoring.
- Externalize strings to support i18n.
