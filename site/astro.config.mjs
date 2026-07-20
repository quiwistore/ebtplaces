import { defineConfig } from 'astro/config';
export default defineConfig({
  site: 'https://ebtplaces.com',
  outDir: '../dist',
  build: { format: 'directory', inlineStylesheets: 'always' }
});
