import { viewerBundle } from './generated/viewerBundle';
export function buildViewerDocument(modelBase64: string): string {
  if (!modelBase64 || !/^[A-Za-z0-9+/]+={0,2}$/.test(modelBase64)) throw new Error('Modèle local invalide.');
  return `<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; connect-src 'none'; worker-src 'none'; base-uri 'none'; form-action 'none'">
<style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#050d16;overscroll-behavior:none}canvas{display:block;width:100%;height:100%;touch-action:none;-webkit-user-select:none;user-select:none}</style></head>
<body><script id="model-data" type="application/octet-stream">${modelBase64}</script><script>${viewerBundle.replace(/<\/script/gi, '<\\/script')}</script></body></html>`;
}
