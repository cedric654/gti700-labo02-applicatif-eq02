// Courtiers privés de démonstration : ne contacte et ne publie jamais sur HiveMQ.
const net = require('node:net');
const http = require('node:http');
const aedes = require('aedes');
const websocket = require('websocket-stream');
const {topics} = require('../domain');
const servers = [], brokers = [], sockets = [];
for (const [tcpPort, wsPort] of [[1883, 9001], [1884, 9002]]) {
  const broker = aedes(), tcp = net.createServer(broker.handle), web = http.createServer();
  sockets.push(websocket.createServer({server: web}, broker.handle));
  for (const server of [tcp, web]) server.on('error', error => { console.error(error.message); shutdown(); process.exitCode = 1; });
  tcp.listen(tcpPort, '127.0.0.1'); web.listen(wsPort, '127.0.0.1');
  servers.push(tcp, web); brokers.push(broker);
  console.info(`Courtier de test : mqtt://127.0.0.1:${tcpPort} et ws://127.0.0.1:${wsPort}`);
}
const palette = ['255;0;0', '0;180;70', '0;90;255']; let index = 0;
const timer = setInterval(() => {
  for (let team = 1; team <= 12; team++) brokers[1].publish({topic: topics(team).alert,
    payload: Buffer.from(palette[(index + team) % palette.length]), qos: 0, retain: false}, () => {});
  index++;
}, 3000);
let stopped = false;
function shutdown() {
  if (stopped) return; stopped = true; clearInterval(timer);
  sockets.forEach(ws => ws.close()); brokers.forEach(broker => broker.close()); servers.forEach(server => server.close());
}
process.once('SIGINT', shutdown); process.once('SIGTERM', shutdown);
