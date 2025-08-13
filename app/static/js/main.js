import { greet } from './utils.js';

document.addEventListener('DOMContentLoaded', () => {
  const message = greet();
  console.log(message);
  const content = document.getElementById('content');
  if (content) {
    const p = document.createElement('p');
    p.textContent = message;
    content.appendChild(p);
  }
});
