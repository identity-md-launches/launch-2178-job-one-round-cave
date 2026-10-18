'use strict';
// Extract only generated pigment; retain the ancestor's rock even inside the patch.
const fs = require('node:fs');
const crypto = require('node:crypto');
const {decodePNG, encodePNG, preview} = require('./finish_wall.js');
if(crypto.createHash('sha256').update(fs.readFileSync('artifacts/line-1/wall.png')).digest('hex') !== '28101e7496a715ce48856c0bbdc00598d363c60b6f378a21748145968a410dbd') throw Error('one-shot compositor: current wall must be the unmodified ancestor');
const ancestor = decodePNG('artifacts/line-1/wall.png');
const pigment = decodePNG('artifacts/line-1/wall-v6.png');
if(pigment.pixels[0]+pigment.pixels[1]+pigment.pixels[2]<600) throw Error('requires original pale-background generated pigment source');
const result = {...ancestor,pixels:Buffer.from(ancestor.pixels)};
const bounds=[525,900,725,1050], source=[240,330,1010,910];
let changed=0;
for(let y=bounds[1];y<bounds[3];y++) for(let x=bounds[0];x<bounds[2];x++) {
  // Average four generator pixels to retain dry-grain gaps at preview scale.
  const colors=[0,0,0];
  for(const dy of [0.25,0.75]) for(const dx of [0.25,0.75]) {
    const sx=Math.floor(source[0]+(x-bounds[0]+dx)/(bounds[2]-bounds[0])*(source[2]-source[0]));
    const sy=Math.floor(source[1]+(y-bounds[1]+dy)/(bounds[3]-bounds[1])*(source[3]-source[1]));
    for(let c=0;c<3;c++) colors[c]+=pigment.pixels[(sy*pigment.width+sx)*pigment.channels+c]/4;
  }
  const [r,g,b]=colors;
  const red=r>g*1.38 && r>b*1.6 && g<125;
  const black=Math.max(r,g,b)<135;
  if(!red && !black) continue;
  const alpha=Math.min(0.78, red ? (r-g)/110 : (150-Math.max(r,g,b))/100);
  const color=red ? [125,47,22] : [40,29,18];
  const at=(y*result.width+x)*result.channels;
  for(let c=0;c<3;c++) result.pixels[at+c]=Math.round(result.pixels[at+c]*(1-alpha)+color[c]*alpha);
  if(!result.pixels.subarray(at,at+3).equals(ancestor.pixels.subarray(at,at+3))) changed++;
}
let outside=true;
for(let y=0;y<result.height;y++) for(let x=0;x<result.width;x++) {
  if(x>=bounds[0] && x<bounds[2] && y>=bounds[1] && y<bounds[3]) continue;
  const at=(y*result.width+x)*result.channels;
  if(!result.pixels.subarray(at,at+result.channels).equals(ancestor.pixels.subarray(at,at+ancestor.channels))) outside=false;
}
if(!outside || changed<100) throw Error('failed preservation or empty pigment');
const png=encodePNG(result), jpg=preview(result);
if(jpg.length>100000) throw Error('preview too large');
fs.writeFileSync('artifacts/line-1/wall-v6.png',png);
fs.writeFileSync('artifacts/line-1/wall.png',png);
fs.writeFileSync('dist/line-1/25.jpg',jpg);
console.log(JSON.stringify({bounds,source,changed_pixels:changed,all_pixels_outside_identical:outside,width:result.width,height:result.height,png_bytes:png.length,jpeg_bytes:jpg.length}));
