import * as esbuild from 'esbuild';

await esbuild.build({
  entryPoints: ['cm6-src/index.js'],
  bundle: true,
  minify: true,
  format: 'iife',
  target: ['es2020'],
  outfile: 'otterwiki/static/js/cm6-bundle.min.js',
  sourcemap: false,
});
