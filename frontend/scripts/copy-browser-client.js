const fs = require('node:fs');
const path = require('node:path');
const directory = path.join(__dirname, '../vendor');
fs.mkdirSync(directory, {recursive: true});
fs.copyFileSync(path.join(__dirname, '../node_modules/mqtt/dist/mqtt.min.js'), path.join(directory, 'mqtt.min.js'));
fs.copyFileSync(path.join(__dirname, '../node_modules/mqtt/LICENSE.md'), path.join(directory, 'MQTT-LICENSE.md'));
console.log('Client MQTT copié : le front-end peut être ouvert avec file://');
