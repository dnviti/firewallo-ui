// On-the-fly convert embedded SVG to ICO for older browsers if needed.
(async ()=>{
  if (document.querySelector('link[rel="icon"][href$="favicon.ico"]')) return;
})();
